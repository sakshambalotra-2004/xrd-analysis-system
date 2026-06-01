/**
 * api/reportApi.js
 * ================
 * Client-side API helpers for the /api/report endpoints.
 */
import axios from "axios";

const BASE = "/api/report";

export const reportApi = {
  /**
   * Return the direct URL to the PDF report for browser download.
   *
   * @param {string} fileId
   * @returns {string} URL
   */
  getPdfUrl(fileId) {
    return `${BASE}/${fileId}`;
  },

  /**
   * Fetch graph image URLs for a completed analysis.
   *
   * @param {string} fileId
   * @returns {Promise<{ experimental: string, standard: string, overlay: string }>}
   */
  async getGraphUrls(fileId) {
    const { data } = await axios.get(`${BASE}/${fileId}/graphs`);
    return data;
  },

  /**
   * Fetch a lightweight JSON summary (no file paths).
   *
   * @param {string} fileId
   * @returns {Promise<object>}
   */
  async getSummary(fileId) {
    const { data } = await axios.get(`${BASE}/${fileId}/summary`);
    return data;
  },

  /**
   * Programmatically trigger a PDF download in the browser.
   *
   * @param {string} fileId
   * @param {string} [filename]
   */
  async downloadPdf(fileId, filename = `xrd_report_${fileId}.pdf`) {
    const response = await axios.get(`${BASE}/${fileId}`, { responseType: "blob" });
    const url = URL.createObjectURL(new Blob([response.data], { type: "application/pdf" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  },
};