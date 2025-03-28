// src/services/PrinterService.ts
import axiosInstance from '../lib/axios';
import axios from 'axios'; // Importamos axios directamente para usarlo en este caso específico

export interface Printer {
  id?: number;
  name: string;
  brand: string;
  model: string;
  ip_address: string;
  status?: string;
  client_id?: number;
  agent_id?: number;
  last_check?: string;
  serial_number?: string;
  printer_data?: any;
}

export interface PrinterSupplies {
  toners: {
    black: number;
    cyan: number;
    magenta: number;
    yellow: number;
  };
  drums: {
    black: number;
    cyan: number;
    magenta: number;
    yellow: number;
  };
}

export interface PrinterCounters {
  total: number;
  color: number;
  black_and_white: number;
  copies: number;
  prints: number;
  scans: number;
}

export interface PrinterReport {
  total_printers: number;
  printers_by_status: Record<string, number>;
  printers_by_brand: Record<string, number>;
  critical_supplies: Array<{
    printer_id: number;
    printer_name: string;
    critical_supplies: any[];
  }>;
}

export class PrinterService {
  static async getPrinters(agentId?: number): Promise<Printer[]> {
    console.log('📞 getPrinters: Iniciando solicitud de impresoras...');
    
    if (agentId) {
      console.log(`📞 getPrinters: Se solicitaron impresoras para el agente ID: ${agentId}`);
    } else {
      console.log('📞 getPrinters: Se solicitaron todas las impresoras');
    }
    
    try {
      // Notar la barra inclinada (/) al final de la URL
      // Esto evita la redirección 307 que está causando el error
      const params = agentId ? { agent_id: agentId } : {};
      console.log('🚀 getPrinters: Realizando solicitud directa a la URL final con / al final');
      const response = await axiosInstance.get('/monitor/printers/', { params });
      
      console.log('✅ getPrinters: Solicitud exitosa');
      
      // Verificar tipo de datos recibidos
      if (response.data) {
        console.log(`📦 getPrinters: Datos recibidos. Tipo: ${typeof response.data}`);
        if (Array.isArray(response.data)) {
          console.log(`📊 getPrinters: Se recibieron ${response.data.length} impresoras`);
        } else {
          console.log(`⚠️ getPrinters: Los datos recibidos no son un array: ${JSON.stringify(response.data).substring(0, 100)}...`);
        }
      } else {
        console.log('⚠️ getPrinters: No se recibieron datos en la respuesta');
      }
      
      return response.data || [];
    } catch (error) {
      console.error("❌ getPrinters: Error al obtener impresoras:", error);
      console.log('📝 getPrinters: Detalles del error:', {
        message: error.message,
        code: error.code,
        status: error.response?.status,
        stack: error.stack
      });
      throw error;
    }
  }

  static async getPrinterById(printerId: number): Promise<Printer | null> {
    console.log(`📞 getPrinterById: Buscando impresora con ID ${printerId}...`);
    try {
      const response = await axiosInstance.get(`/monitor/printers/${printerId}`);
      console.log(`✅ getPrinterById: Impresora ${printerId} encontrada`);
      return response.data;
    } catch (error) {
      console.error(`❌ getPrinterById: Error al buscar impresora ${printerId}:`, error);
      return null;
    }
  }

  static async createPrinter(printerData: Printer): Promise<Printer> {
    console.log(`📞 createPrinter: Creando nueva impresora...`, printerData);
    try {
      const response = await axiosInstance.post('/monitor/printers/create', printerData);
      console.log(`✅ createPrinter: Impresora creada con éxito`);
      return response.data;
    } catch (error) {
      console.error("❌ createPrinter: Error al crear impresora:", error);
      throw error;
    }
  }

  static async updatePrinter(printerId: number, printerData: Partial<Printer>): Promise<Printer> {
    console.log(`📞 updatePrinter: Actualizando impresora ${printerId}...`, printerData);
    try {
      const response = await axiosInstance.post('/monitor/printers/update', {
        ...printerData,
        printer_id: printerId,
        agent_id: printerData.agent_id || 1
      });
      console.log(`✅ updatePrinter: Impresora ${printerId} actualizada`);
      return response.data;
    } catch (error) {
      console.error(`❌ updatePrinter: Error al actualizar impresora ${printerId}:`, error);
      throw error;
    }
  }

  static async deletePrinter(printerId: number): Promise<boolean> {
    console.log(`📞 deletePrinter: Eliminando impresora ${printerId}...`);
    try {
      await axiosInstance.delete(`/monitor/printers/${printerId}`);
      console.log(`✅ deletePrinter: Impresora ${printerId} eliminada`);
      return true;
    } catch (error) {
      console.error(`❌ deletePrinter: Error al eliminar impresora ${printerId}:`, error);
      return false;
    }
  }

  static async getPrinterSupplies(printerId: number): Promise<PrinterSupplies | null> {
    console.log(`📞 getPrinterSupplies: Obteniendo suministros para impresora ${printerId}...`);
    try {
      const response = await axiosInstance.get(`/monitor/printers/${printerId}/supplies`);
      console.log(`✅ getPrinterSupplies: Suministros obtenidos para impresora ${printerId}`);
      return response.data.supplies;
    } catch (error) {
      console.error(`❌ getPrinterSupplies: Error al obtener suministros para impresora ${printerId}:`, error);
      return null;
    }
  }

  static async getPrinterCounters(printerId: number): Promise<PrinterCounters | null> {
    console.log(`📞 getPrinterCounters: Obteniendo contadores para impresora ${printerId}...`);
    try {
      const response = await axiosInstance.get(`/monitor/printers/${printerId}/counters`);
      console.log(`✅ getPrinterCounters: Contadores obtenidos para impresora ${printerId}`);
      return response.data.counters;
    } catch (error) {
      console.error(`❌ getPrinterCounters: Error al obtener contadores para impresora ${printerId}:`, error);
      return null;
    }
  }

  static async getPrinterHistory(printerId: number, days: number = 7): Promise<any> {
    console.log(`📞 getPrinterHistory: Obteniendo historial para impresora ${printerId} (${days} días)...`);
    try {
      const response = await axiosInstance.get(`/monitor/printers/${printerId}/history`, {
        params: { days }
      });
      console.log(`✅ getPrinterHistory: Historial obtenido para impresora ${printerId}`);
      return response.data;
    } catch (error) {
      console.error(`❌ getPrinterHistory: Error al obtener historial para impresora ${printerId}:`, error);
      return null;
    }
  }

  static async getPrinterReport(): Promise<PrinterReport | null> {
    console.log(`📞 getPrinterReport: Obteniendo informe de impresoras...`);
    try {
      const response = await axiosInstance.get('/monitor/printers/report');
      console.log(`✅ getPrinterReport: Informe de impresoras obtenido`);
      return response.data;
    } catch (error) {
      console.error("❌ getPrinterReport: Error al obtener informe de impresoras:", error);
      return null;
    }
  }

  static async getCriticalSupplies(): Promise<any[]> {
    console.log(`📞 getCriticalSupplies: Obteniendo suministros críticos...`);
    try {
      const response = await axiosInstance.get('/monitor/printers/critical-supplies');
      console.log(`✅ getCriticalSupplies: Suministros críticos obtenidos`);
      return response.data || [];
    } catch (error) {
      console.error("❌ getCriticalSupplies: Error al obtener suministros críticos:", error);
      return [];
    }
  }

  static async updatePrinterData(printerId: number, printerData: any, agentId?: number): Promise<Printer> {
    console.log(`📞 updatePrinterData: Actualizando datos para impresora ${printerId}...`);
    try {
      const response = await axiosInstance.post('/monitor/printers/update', {
        printer_data: printerData,
        agent_id: agentId || 1
      });
      console.log(`✅ updatePrinterData: Datos actualizados para impresora ${printerId}`);
      return response.data;
    } catch (error) {
      console.error(`❌ updatePrinterData: Error al actualizar datos de impresora ${printerId}:`, error);
      throw error;
    }
  }
  
  static async countByStatus(): Promise<Record<string, number>> {
    console.log(`📞 countByStatus: Contando impresoras por estado...`);
    try {
      const printers = await this.getPrinters();
      
      const result = {
        total: printers.length,
        online: 0,
        offline: 0,
        error: 0
      };
      
      printers.forEach(printer => {
        if (printer.status === 'online') result.online++;
        else if (printer.status === 'offline') result.offline++;
        else if (printer.status === 'error') result.error++;
      });
      
      console.log(`✅ countByStatus: Conteo completado -`, result);
      return result;
    } catch (error) {
      console.error("❌ countByStatus: Error al contar impresoras por estado:", error);
      return {
        total: 0,
        online: 0,
        offline: 0,
        error: 0
      };
    }
  }
  
  static async getPrintersByClient(clientId: number): Promise<Printer[]> {
    console.log(`📞 getPrintersByClient: Buscando impresoras para cliente ${clientId}...`);
    try {
      const printers = await this.getPrinters();
      const clientPrinters = printers.filter(printer => printer.client_id === clientId);
      console.log(`✅ getPrintersByClient: Encontradas ${clientPrinters.length} impresoras para cliente ${clientId}`);
      return clientPrinters;
    } catch (error) {
      console.error(`❌ getPrintersByClient: Error al buscar impresoras para cliente ${clientId}:`, error);
      return [];
    }
  }
}