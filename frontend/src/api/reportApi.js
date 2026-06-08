/**
 * api/reportApi.js
 * ================
 * Client-side API helpers for the /api/report endpoints.
 */

import axios from "axios";

const BASE = "http://127.0.0.1:8000/api/report";

export const reportApi = {
  /**
   * Return direct PDF URL
   */
  getPdfUrl(fileId) {
    return `${BASE}/${fileId}`;
  },

  /**
   * Fetch graph image URLs
   */
  async getGraphUrls(fileId) {
    const { data } = await axios.get(
      `${BASE}/${fileId}/graphs`
    );

    return data;
  },

  /**
   * Fetch summary
   */
  async getSummary(fileId) {
    const { data } = await axios.get(
      `${BASE}/${fileId}/summary`
    );

    return data;
  },

  /**
   * Download PDF
   */
  async downloadPdf(
    fileId,
    filename = `xrd_report_${fileId}.pdf`
  ) {
    const response = await axios.get(
      `${BASE}/${fileId}`,
      {
        responseType: "blob",
      }
    );

    const url = URL.createObjectURL(
      new Blob([response.data], {
        type: "application/pdf",
      })
    );

    const a = document.createElement("a");

    a.href = url;
    a.download = filename;

    document.body.appendChild(a);

    a.click();

    a.remove();

    URL.revokeObjectURL(url);
  },
};