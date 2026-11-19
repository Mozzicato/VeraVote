export type Place = { id: number; name: string; code: string };

export type PollingUnit = {
  id: number;
  official_code: string;
  official_name: string;
  unit_number: string;
  location_description: string;
  aliases: string[];
  ward: Place;
  lga: Place;
  state: Place;
  latitude: number | null;
  longitude: number | null;
  dataset_source: string;
  dataset_version: string;
  last_verified: string | null;
  is_simulated: boolean;
  matched_alias?: string | null;
};

export type Contest = {
  id: number;
  office: string;
  constituency: string;
  election: { id: number; name: string; date: string; is_simulated: boolean };
  candidates: { id: number; party: string; name: string }[];
};

export type Flag = { check: string; expected: string | number; found: number; message: string; source?: string; label?: string };

export type Source = {
  ref: string;
  kind: "submission" | "official";
  id: number;
  classification: string;
  label: string;
  organisation_name: string | null;
  file_hash: string | null;
  is_forwarded_copy: string;
  status: string;
  received_at: string;
  comparable: boolean;
  values: Record<string, number | null>;
  arithmetic_flags: Flag[];
  source_reference?: string;
  version_reference?: string;
  file_available?: boolean;
};

export type Comparison = {
  a: string;
  b: string;
  a_label: string;
  b_label: string;
  result: "agree" | "differ" | "not_comparable";
  independent: boolean;
  fields_compared: number;
  differences: { field_key: string; label: string; a: number; b: number; difference: number }[];
};

export type Evaluation = {
  status: StatusKey;
  status_title: string;
  explanation: string;
  notes: string[];
  disclaimer: string;
  fields: { key: string; label: string }[];
  sources: Source[];
  documents: { key: string; kind: string; label: string; values: Record<string, number | null>; contributors: number; organisations: number; forwarded: boolean; sources?: string[] }[];
  comparisons: Comparison[];
  independence: {
    submissions: number;
    distinct_contributors: number;
    distinct_organisations: number;
    distinct_documents: number;
    official_documents: number;
    comparable_documents: number;
    notes: string[];
  };
  arithmetic_flags: Flag[];
  investigation: { id: number; status: string; outcome: string | null; public_summary: string } | null;
};

export type StatusKey =
  | "no_evidence"
  | "evidence_received"
  | "under_review"
  | "consistent_evidence"
  | "discrepancy_detected"
  | "insufficient_evidence"
  | "review_completed";

export type UnitPage = {
  polling_unit: PollingUnit;
  contests: ({ contest: Contest } & Evaluation)[];
  timeline: { at: string; event: string; by: string; event_hash: string }[];
  simulated: boolean;
};

export type Receipt = {
  receipt_code: string;
  submission_id: number;
  client_submission_id: string;
  polling_unit: { id: number; code: string; name: string };
  contest_id: number;
  classification: string;
  classification_label: string;
  file_sha256: string | null;
  file_size: number | null;
  server_received_time: string;
  device_reported_time: string | null;
  device_time_note: string;
  captured_offline: boolean;
  status: string;
  duplicate_retry: boolean;
  hash_note: string;
  review_note?: string;
};

export type DemoUser = { id: number; name: string; role: string; persona: string; classification: string; organisation_id: number | null };
