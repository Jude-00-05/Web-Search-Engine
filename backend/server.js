const express = require("express");
const cors = require("cors");
const fs = require("fs");
const path = require("path");
const { deepSearchDatasets } = require("./liveSearch");

const app = express();
const PORT = process.env.PORT || 3001;
const DATA_DIR = path.join(__dirname, "..", "data");
const DATASETS_PATH = path.join(DATA_DIR, "merged_datasets.json");
const INDEX_PATH = path.join(DATA_DIR, "inverted_index.json");
const STOPWORDS_PATH = path.join(DATA_DIR, "stopwords.txt");
const FIELD_WEIGHTS = {
  title: 3,
  tags: 2,
  task_types: 2,
  description: 1,
  formats: 1,
};
const GENERIC_QUERY_TERMS = new Set(["dataset", "datasets", "data", "file", "files"]);
const EXPLICIT_FORMAT_TERMS = new Set(["csv", "json", "parquet", "zip", "tsv"]);
const PHRASE_BOOSTS = {
  title: 28,
  tags: 22,
  description: 16,
};
const TERM_BOOSTS = {
  title: 6,
  tags: 5,
  task_types: 4,
  formats: 4,
  description: 1.5,
};
const SOURCE_INTENT_WEIGHTS = {
  kaggle: 2.5,
  huggingface: 2.5,
  uci: 1.8,
  openml: 1.8,
  mendeley: 1.5,
  github: 0.5,
  datagov: -0.5,
};
const INTENT_PROFILES = [
  {
    name: "mental_health",
    triggers: [
      "mental health",
      "depression",
      "anxiety",
      "stress",
      "wellbeing",
      "psychology",
      "behavioral health",
      "behavioural health",
    ],
    expansionTerms: [
      "depression",
      "anxiety",
      "stress",
      "wellbeing",
      "psychology",
      "behavioral health",
      "behavioural health",
      "questionnaire",
      "survey",
      "student mental health",
      "suicide",
      "therapy",
      "wellness",
    ],
    negativeTerms: [
      "dispatch",
      "911",
      "ems",
      "fire",
      "county",
      "census",
      "tract",
      "shortage",
      "hpsa",
      "address",
      "service area",
      "provider",
      "infrastructure",
      "facility",
      "administrative",
      "public safety",
      "emergency response",
    ],
    sourceAdjustments: {
      kaggle: 4,
      huggingface: 4,
      uci: 3,
      github: 1,
      datagov: -3,
    },
  },
];

app.use(cors());

function readJson(filePath, fallback) {
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch (error) {
    return fallback;
  }
}

function readStopwords() {
  try {
    const content = fs.readFileSync(STOPWORDS_PATH, "utf8");
    return new Set(
      content
        .split(/\r?\n/)
        .map((word) => word.trim())
        .filter(Boolean)
    );
  } catch (error) {
    return new Set();
  }
}

function stemToken(token) {
  if (token.length <= 3) {
    return token;
  }

  return token
    .replace(/(ing|edly|ed|ly|ment|ments)$/i, "")
    .replace(/(ies)$/i, "y")
    .replace(/(s)$/i, "");
}

function tokenize(text, stopwords) {
  return (text.toLowerCase().match(/[a-z0-9]+/g) || [])
    .filter((token) => !stopwords.has(token))
    .map((token) => stemToken(token));
}

function rawTokens(text) {
  return (String(text || "").toLowerCase().match(/[a-z0-9]+/g) || []);
}

function joinFieldValue(value) {
  return Array.isArray(value) ? value.join(" ") : String(value || "");
}

function buildQuerySignals(query, stopwords) {
  const raw = rawTokens(query);
  const stemmed = tokenize(query, stopwords);
  const weightedTerms = raw.map((token, index) => ({
    raw: token,
    stemmed: stemmed[index] || stemToken(token),
    weight: GENERIC_QUERY_TERMS.has(token) ? 0.2 : 1,
    isFormat: EXPLICIT_FORMAT_TERMS.has(token),
  }));

  const normalizedWords = raw.filter((token) => !GENERIC_QUERY_TERMS.has(token));
  const phrases = [];
  const fullPhrase = normalizedWords.join(" ").trim();
  if (fullPhrase.split(" ").length > 1) {
    phrases.push(fullPhrase);
  }
  for (let i = 0; i < normalizedWords.length - 1; i += 1) {
    const phrase = `${normalizedWords[i]} ${normalizedWords[i + 1]}`.trim();
    if (phrase && !phrases.includes(phrase)) {
      phrases.push(phrase);
    }
  }

  const loweredQuery = query.trim().toLowerCase();
  const activeIntents = INTENT_PROFILES.filter((profile) =>
    profile.triggers.some((trigger) => loweredQuery.includes(trigger))
  );

  return { weightedTerms, phrases, fullPhrase, activeIntents };
}

function scoreFieldMatches(text, terms, baseBoost) {
  const lower = String(text || "").toLowerCase();
  let score = 0;
  let matchedSpecificTerms = 0;

  for (const term of terms) {
    if (!term.raw || !lower.includes(term.raw)) {
      continue;
    }
    const weightedBoost = baseBoost * term.weight;
    score += weightedBoost;
    if (term.weight >= 1) {
      matchedSpecificTerms += 1;
    }
  }

  return { score, matchedSpecificTerms };
}

function scorePhraseMatches(text, phrases, boost) {
  const lower = String(text || "").toLowerCase();
  let score = 0;
  let matches = 0;

  for (const phrase of phrases) {
    if (phrase && lower.includes(phrase)) {
      score += boost;
      matches += 1;
    }
  }

  return { score, matches };
}

function scoreIntentExpansion(text, activeIntents) {
  const lower = String(text || "").toLowerCase();
  let score = 0;

  for (const profile of activeIntents) {
    for (const term of profile.expansionTerms) {
      if (lower.includes(term)) {
        score += term.includes(" ") ? 4.5 : 2;
      }
    }
  }

  return score;
}

function scoreIntentPenalty(text, activeIntents) {
  const lower = String(text || "").toLowerCase();
  let penalty = 0;

  for (const profile of activeIntents) {
    for (const term of profile.negativeTerms) {
      if (lower.includes(term)) {
        penalty += term.includes(" ") ? 5 : 3;
      }
    }
  }

  return penalty;
}

function buildRuntimeIndex(datasets, stopwords) {
  const terms = {};
  const searchableFields = ["title", "description", "tags", "task_types", "formats"];

  datasets.forEach((dataset, docId) => {
    searchableFields.forEach((field) => {
      const rawValue = dataset[field];
      const text = Array.isArray(rawValue) ? rawValue.join(" ") : String(rawValue || "");
      const counts = {};
      tokenize(text, stopwords).forEach((token) => {
        counts[token] = (counts[token] || 0) + 1;
      });

      Object.entries(counts).forEach(([token, count]) => {
        if (!terms[token]) {
          terms[token] = {
            title: {},
            description: {},
            tags: {},
            task_types: {},
            formats: {},
          };
        }
        terms[token][field][String(docId)] = count;
      });
    });
  });

  return {
    metadata: {
      document_count: datasets.length,
      search_fields: searchableFields,
    },
    terms,
  };
}

function loadDataStore() {
  const datasets = readJson(DATASETS_PATH, []);
  const stopwords = readStopwords();
  const storedIndex = readJson(INDEX_PATH, { metadata: {}, terms: {} });
  const index =
    storedIndex &&
    storedIndex.terms &&
    Object.keys(storedIndex.terms).length > 0 &&
    Number(storedIndex.metadata?.document_count || 0) === datasets.length
      ? storedIndex
      : buildRuntimeIndex(datasets, stopwords);

  return { datasets, stopwords, index };
}

let dataStore = loadDataStore();

function refreshStore() {
  dataStore = loadDataStore();
  return dataStore;
}

function toArrayParam(value) {
  if (!value) {
    return [];
  }
  if (Array.isArray(value)) {
    return value.flatMap((item) => String(item).split(",")).map((item) => item.trim()).filter(Boolean);
  }
  return String(value)
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function matchesFilters(dataset, filters) {
  const sourceMatch =
    filters.sources.length === 0 || filters.sources.includes(dataset.source.toLowerCase());
  const formatMatch =
    filters.formats.length === 0 ||
    dataset.formats.some((format) => filters.formats.includes(String(format).toLowerCase()));
  const taskMatch =
    filters.tasks.length === 0 ||
    dataset.task_types.some((task) => filters.tasks.includes(String(task).toLowerCase()));

  return sourceMatch && formatMatch && taskMatch;
}

function searchDatasets(query, filters) {
  const { datasets, stopwords, index } = dataStore;
  const { weightedTerms, phrases, fullPhrase, activeIntents } = buildQuerySignals(query, stopwords);
  const tokens = weightedTerms.map((term) => term.stemmed).filter(Boolean);
  const candidateIds = new Set();
  const termEntries = Object.entries(index.terms || {});

  tokens.forEach((token) => {
    const matchingTerms = termEntries.filter(([term]) => term === token || term.startsWith(token));

    matchingTerms.forEach(([term, postings]) => {
      Object.keys(FIELD_WEIGHTS).forEach((field) => {
        const fieldPostings = postings[field] || {};
        Object.keys(fieldPostings).forEach((docId) => candidateIds.add(docId));
      });
    });
  });

  const idsToScore = candidateIds.size > 0 ? Array.from(candidateIds) : datasets.map((_, indexValue) => String(indexValue));

  const results = idsToScore
    .map((docId) => {
      const dataset = datasets[Number(docId)];
      if (!dataset) {
        return null;
      }

      const titleText = joinFieldValue(dataset.title);
      const tagText = joinFieldValue(dataset.tags);
      const taskText = joinFieldValue(dataset.task_types);
      const formatText = joinFieldValue(dataset.formats);
      const descriptionText = joinFieldValue(dataset.description);

      let score = 0;
      let matchedSpecificTerms = 0;

      const titleTerms = scoreFieldMatches(titleText, weightedTerms, TERM_BOOSTS.title);
      const tagTerms = scoreFieldMatches(tagText, weightedTerms, TERM_BOOSTS.tags);
      const taskTerms = scoreFieldMatches(taskText, weightedTerms, TERM_BOOSTS.task_types);
      const formatTerms = scoreFieldMatches(formatText, weightedTerms, TERM_BOOSTS.formats);
      const descriptionTerms = scoreFieldMatches(descriptionText, weightedTerms, TERM_BOOSTS.description);

      score += titleTerms.score + tagTerms.score + taskTerms.score + formatTerms.score + descriptionTerms.score;
      matchedSpecificTerms +=
        titleTerms.matchedSpecificTerms +
        tagTerms.matchedSpecificTerms +
        taskTerms.matchedSpecificTerms +
        formatTerms.matchedSpecificTerms +
        descriptionTerms.matchedSpecificTerms;

      const titlePhrases = scorePhraseMatches(titleText, phrases, PHRASE_BOOSTS.title);
      const tagPhrases = scorePhraseMatches(tagText, phrases, PHRASE_BOOSTS.tags);
      const descriptionPhrases = scorePhraseMatches(descriptionText, phrases, PHRASE_BOOSTS.description);

      score += titlePhrases.score + tagPhrases.score + descriptionPhrases.score;

      if (fullPhrase && titleText.toLowerCase().includes(fullPhrase)) {
        score += 12;
      }

      const requestedFormats = weightedTerms.filter((term) => term.isFormat);
      for (const formatTerm of requestedFormats) {
        if (dataset.formats.some((format) => String(format).toLowerCase() === formatTerm.raw)) {
          score += 10;
        } else {
          score -= 2;
        }
      }

      score += scoreIntentExpansion(titleText, activeIntents) * 2;
      score += scoreIntentExpansion(tagText, activeIntents) * 1.5;
      score += scoreIntentExpansion(descriptionText, activeIntents);

      const negativePenalty =
        scoreIntentPenalty(titleText, activeIntents) * 1.2 +
        scoreIntentPenalty(tagText, activeIntents) +
        scoreIntentPenalty(descriptionText, activeIntents) * 0.8;
      score -= negativePenalty;

      score += SOURCE_INTENT_WEIGHTS[dataset.source] || 0;
      for (const profile of activeIntents) {
        score += profile.sourceAdjustments?.[dataset.source] || 0;
      }

      if (dataset.source === "datagov" && matchedSpecificTerms < 2 && descriptionPhrases.matches === 0) {
        score -= 3;
      }

      if (
        matchedSpecificTerms === 0 &&
        titlePhrases.matches === 0 &&
        tagPhrases.matches === 0 &&
        descriptionPhrases.matches === 0
      ) {
        score -= 5;
      }

      return {
        ...dataset,
        score: Number(score.toFixed(2)),
      };
    })
    .filter(Boolean)
    .filter((dataset) => dataset && matchesFilters(dataset, filters))
    .filter((dataset) => dataset.score > 0)
    .sort((left, right) => {
      if (right.score !== left.score) {
        return right.score - left.score;
      }
      return right.downloads - left.downloads;
    });

  return results;
}

function collectAvailableFilters(datasets) {
  const sources = {};
  const formats = {};
  const taskTypes = {};

  datasets.forEach((dataset) => {
    sources[dataset.source] = (sources[dataset.source] || 0) + 1;
    dataset.formats.forEach((format) => {
      formats[format] = (formats[format] || 0) + 1;
    });
    dataset.task_types.forEach((task) => {
      taskTypes[task] = (taskTypes[task] || 0) + 1;
    });
  });

  return { sources, formats, task_types: taskTypes };
}

app.get("/api/health", (req, res) => {
  res.json({
    status: "ok",
    datasets: dataStore.datasets.length,
    indexedTerms: Object.keys(dataStore.index.terms || {}).length,
  });
});

app.get("/api/search", (req, res) => {
  const query = String(req.query.q || "").trim();
  const filters = {
    sources: toArrayParam(req.query.sources).map((value) => value.toLowerCase()),
    formats: toArrayParam(req.query.formats).map((value) => value.toLowerCase()),
    tasks: toArrayParam(req.query.tasks).map((value) => value.toLowerCase()),
  };

  if (!query) {
    const filteredDatasets = dataStore.datasets.filter((dataset) => matchesFilters(dataset, filters));
    return res.json({
      query,
      total: filteredDatasets.length,
      results: filteredDatasets.slice(0, 24),
      available_filters: collectAvailableFilters(filteredDatasets),
    });
  }

  const results = searchDatasets(query, filters);
  return res.json({
    query,
    total: results.length,
    results,
    available_filters: collectAvailableFilters(results),
  });
});

app.get("/api/datasets", (req, res) => {
  const page = Math.max(Number(req.query.page) || 1, 1);
  const limit = Math.min(Math.max(Number(req.query.limit) || 12, 1), 48);
  const filters = {
    sources: toArrayParam(req.query.sources).map((value) => value.toLowerCase()),
    formats: toArrayParam(req.query.formats).map((value) => value.toLowerCase()),
    tasks: toArrayParam(req.query.tasks).map((value) => value.toLowerCase()),
  };

  const filtered = dataStore.datasets.filter((dataset) => matchesFilters(dataset, filters));
  const sorted = [...filtered].sort((left, right) => right.downloads - left.downloads);
  const start = (page - 1) * limit;

  res.json({
    page,
    limit,
    total: sorted.length,
    results: sorted.slice(start, start + limit),
    available_filters: collectAvailableFilters(sorted),
  });
});

app.get("/api/sources", (req, res) => {
  const counts = dataStore.datasets.reduce((accumulator, dataset) => {
    accumulator[dataset.source] = (accumulator[dataset.source] || 0) + 1;
    return accumulator;
  }, {});

  const sources = Object.entries(counts).map(([source, count]) => ({ source, count }));
  res.json({ sources });
});

app.get("/api/deep-search", async (req, res) => {
  const query = String(req.query.q || "").trim();
  if (!query) {
    return res.status(400).json({ error: "Missing search query." });
  }

  try {
    const payload = await deepSearchDatasets(query);
    return res.json(payload);
  } catch (error) {
    console.error("[deep-search] request failed", error);
    return res.status(502).json({
      error: "Deep Search is temporarily unavailable.",
      query,
      total: 0,
      results: [],
      sources: [],
    });
  }
});

app.post("/api/reload", (req, res) => {
  const nextStore = refreshStore();
  res.json({
    status: "reloaded",
    datasets: nextStore.datasets.length,
    indexedTerms: Object.keys(nextStore.index.terms || {}).length,
  });
});

app.listen(PORT, () => {
  console.log(`Dataset search API running on port ${PORT}`);
});
