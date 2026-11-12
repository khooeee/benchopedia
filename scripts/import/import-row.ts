/** A result pulled from an outside dataset, before it is matched to our models. */
export type ImportRow = {
  /** Canonical model name as the source gives it, without effort or setting suffixes. */
  modelName: string;
  /** Other names the source uses for the same model (API ids, versions). */
  modelAliases: string[];
  developer?: string;
  released?: string;
  openWeights?: boolean;
  /** Raw value; percentages may be fractions (0–1) and are normalised per series later. */
  value: number;
  date: string;
  effort?: string;
  reportedBy: "benchmark-author" | "model-developer" | "third-party";
  via: string;
  source: string;
};
