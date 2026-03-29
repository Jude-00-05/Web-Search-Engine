import { render, screen } from "@testing-library/react";
import App from "./App";

beforeEach(() => {
  global.fetch = jest.fn((url) => {
    if (String(url).includes("/api/sources")) {
      return Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            sources: [
              { source: "huggingface", count: 3 },
              { source: "uci", count: 3 },
            ],
          }),
      });
    }

    if (String(url).includes("/api/deep-search")) {
      return Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            total: 1,
            results: [
              {
                id: "deep-hf-1",
                title: "Live Beans Dataset",
                description: "Live result from a remote source.",
                source: "huggingface",
                url: "https://huggingface.co/datasets/beans",
                tags: ["live"],
                formats: ["image"],
                task_types: ["classification"],
                downloads: 456,
                score: 12,
                deep: true,
                license: "apache-2.0",
                size: "1,295 images",
                last_updated: "2025-02-18",
              },
            ],
            sources: [{ source: "huggingface", ok: true, count: 1 }],
          }),
      });
    }

    return Promise.resolve({
      ok: true,
      json: () =>
        Promise.resolve({
          total: 1,
          results: [
            {
              id: "hf-beans",
              title: "Beans Image Classification",
              description: "Dataset for bean leaf disease classification.",
              source: "huggingface",
              url: "https://huggingface.co/datasets/beans",
              tags: ["agriculture"],
              formats: ["image"],
              task_types: ["classification"],
              downloads: 123,
              score: 7,
              license: "apache-2.0",
              size: "1,295 images",
              last_updated: "2025-02-18",
            },
          ],
          available_filters: {
            sources: { huggingface: 1 },
            formats: { image: 1 },
            task_types: { classification: 1 },
          },
        }),
    });
  });
});

afterEach(() => {
  jest.resetAllMocks();
});

test("renders the dataset search experience", async () => {
  render(<App />);

  expect(screen.getByText(/find the right dataset faster/i)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /search datasets/i })).toBeInTheDocument();
  expect(screen.getByLabelText(/search datasets/i)).toBeInTheDocument();
  expect(await screen.findByText(/beans image classification/i)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /deep search more datasets/i })).toBeInTheDocument();
});
