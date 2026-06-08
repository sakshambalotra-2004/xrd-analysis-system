/**
 * api/uploadApi.js
 * ================
 * Client-side API helpers for the /api/upload endpoints.
 */

import axios from "axios";

const BASE = "http://127.0.0.1:8000/api/upload";

export const uploadApi = {
  /**
   * Upload an XRD CSV file
   */
  async uploadCSV(file) {
    const formData = new FormData();

    formData.append("file", file);

    const { data } = await axios.post(
      `${BASE}/csv`,
      formData,
      {
        headers: {
          "Content-Type":
            "multipart/form-data",
        },
      }
    );

    return data;
  },

  /**
   * Get upload status
   */
  async getStatus(fileId) {
    const { data } = await axios.get(
      `${BASE}/status/${fileId}`
    );

    return data;
  },

  /**
   * Delete uploaded file
   */
  async deleteUpload(fileId) {
    await axios.delete(
      `${BASE}/${fileId}`
    );
  },
};