// Mirrors backend/app/decisions/schemas.py

export interface LifeSafetyGuidance {
  event_id: string;
  guidance_text: string;
  evidence_ref: string;
  approved: boolean;
}

export interface PolicyExposure {
  policy_id: string;
  tiv_usd: number;
  limit_usd: number;
  deductible_usd: number;
  estimated_exposure_usd: number;
}

export interface InsurerExposureReport {
  event_id: string;
  policies: PolicyExposure[];
  total_estimated_exposure_usd: number;
  evidence_ref: string;
  approved: boolean;
}
