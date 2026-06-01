/**
 * api/uploadApi.js
 * ================
 * Client-side API helpers for the /api/upload endpoints.
 */
import axios from "axios";

const BASE = "/api/upload";

export const uploadApi = {
  /**
   * Upload an XRD CSV file.
   *
   * @param {File} file  — File object from the dropzone / input
   * @returns {Promise<UploadResponse>}
   */
  async uploadCSV(file) {
    const formData = new FormData();
    formData.append("file", file);
    const { data } = await axios.post(`${BASE}/csv`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  },

  /**
   * Get upload status / metadata for a file_id.
   *
   * @param {string} fileId
   * @returns {Promise<UploadStatusResponse>}
   */
  async getStatus(fileId) {
    const { data } = await axios.get(`${BASE}/status/${fileId}`);
    return data;
  },

  /**
   * Delete an uploaded file and its database record.
   *
   * @param {string} fileId
   */
  async deleteUpload(fileId) {
    await axios.delete(`${BASE}/${fileId}`);
  },
};