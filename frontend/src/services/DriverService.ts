import axiosInstance from '../lib/axios';

export interface Driver {
  id: number;
  manufacturer: string;
  model: string;
  driver_filename: string;
  description: string;
}

class DriverService {
  private endpoint = '/drivers';

  async getAll(): Promise<Driver[]> {
    console.log('[DriverService] 🔍 getAll - Iniciando solicitud...');
    try {
      const response = await axiosInstance.get(this.endpoint);
      console.log('[DriverService] ✅ getAll - Datos recibidos:', response.data);
      return response.data;
    } catch (error) {
      console.error('[DriverService] ❌ getAll - Error al obtener drivers:', error);
      throw error;
    }
  }

  async getById(id: number): Promise<Driver> {
    console.log(`[DriverService] 🔍 getById(${id}) - Iniciando solicitud...`);
    try {
      const response = await axiosInstance.get(`${this.endpoint}/${id}`);
      console.log(`[DriverService] ✅ getById(${id}) - Driver recibido:`, response.data);
      return response.data;
    } catch (error) {
      console.error(`[DriverService] ❌ getById(${id}) - Error al obtener driver:`, error);
      throw error;
    }
  }

  async create(formData: FormData): Promise<any> {
    console.log('[DriverService] 🛠️ create - Enviando formulario para nuevo driver...');
    try {
      const response = await axiosInstance.post(this.endpoint, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      console.log('[DriverService] ✅ create - Driver creado:', response.data);
      return response.data;
    } catch (error) {
      console.error('[DriverService] ❌ create - Error al crear driver:', error);
      throw error;
    }
  }

  async update(id: number, formData: FormData): Promise<any> {
    console.log(`[DriverService] 🛠️ update(${id}) - Enviando formulario para actualizar driver...`);
    try {
      const response = await axiosInstance.put(`${this.endpoint}/${id}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      console.log(`[DriverService] ✅ update(${id}) - Driver actualizado:`, response.data);
      return response.data;
    } catch (error) {
      console.error(`[DriverService] ❌ update(${id}) - Error al actualizar driver:`, error);
      throw error;
    }
  }

  async delete(id: number): Promise<any> {
    console.log(`[DriverService] 🗑️ delete(${id}) - Enviando solicitud de eliminación...`);
    try {
      const response = await axiosInstance.delete(`${this.endpoint}/${id}`);
      console.log(`[DriverService] ✅ delete(${id}) - Driver eliminado:`, response.data);
      return response.data;
    } catch (error) {
      console.error(`[DriverService] ❌ delete(${id}) - Error al eliminar driver:`, error);
      throw error;
    }
  }

  getDownloadUrl(id: number): string {
    const url = `https://copierconnectremote.com/api/v1${this.endpoint}/agents/drivers/download/${id}`;
    console.log(`[DriverService] 🔗 getDownloadUrl(${id}) - URL generada: ${url}`);
    return url;
  }
}

export default new DriverService();
