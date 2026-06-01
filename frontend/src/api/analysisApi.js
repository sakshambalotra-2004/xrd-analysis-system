/**
 * api/analysisApi.js
 * ==================
 * Client-side API helpers for the /api/analysis endpoints.
 */
import axios from "axios";

const BASE = "/api/analysis";

export const analysisApi = {
  /**
   * Trigger the full 10-stage XRD analysis pipeline for an uploaded file.
   *
   * @param {string} fileId
   * @returns {Promise<AnalysisResponse>}
   */
  async runAnalysis(fileId) {
    const { data } = await axios.post(`${BASE}/${fileId}`);
    return data;
  },

  /**
   * Retrieve stored analysis results (does not re-run the pipeline).
   *
   * @param {string} fileId
   * @returns {Promise<AnalysisResponse>}
   */
  async getAnalysis(fileId) {
    const { data } = await axios.get(`${BASE}/${fileId}`);
    return data;
  },

  /**
   * List all standard compounds available in the database.
   *
   * @returns {Promise<{ total: number, compounds: Array<{compound_name, formula}> }>}
   */
  async listCompounds() {
    const { data } = await axios.get(`${BASE}/compounds`);
    return data;
  },
};