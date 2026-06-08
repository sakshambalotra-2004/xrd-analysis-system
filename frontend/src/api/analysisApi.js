/**
 * api/analysisApi.js
 * ==================
 * Client-side API helpers for the /api/analysis endpoints.
 */

import axios from "axios";

const BASE = "http://127.0.0.1:8000/api/analysis";

export const analysisApi = {
  /**
   * Trigger the full 10-stage XRD analysis pipeline
   */
  async runAnalysis(fileId) {
    const { data } = await axios.post(
      `${BASE}/${fileId}`
    );

    return data;
  },

  /**
   * Retrieve stored analysis results
   */
  async getAnalysis(fileId) {
    const { data } = await axios.get(
      `${BASE}/${fileId}`
    );

    return data;
  },

  /**
   * List all standard compounds
   */
  async listCompounds() {
    const { data } = await axios.get(
      `${BASE}/compounds`
    );

    return data;
  },

  /**
   * Fetch recent history
   */
  async getRecentHistory(limit = 5) {
    const { data } = await axios.get(
      `${BASE}/history/recent?limit=${limit}`
    );

    return data.history;
  },

  /**
   * Delete analysis
   */
  async deleteAnalysis(fileId) {
    const { data } = await axios.delete(
      `${BASE}/${fileId}`
    );

    return data;
  },
};