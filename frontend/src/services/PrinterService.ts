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
      // Obtener encabezados de autorización del axiosInstance principal
      console.log('🔑 getPrinters: Extrayendo encabezados de autorización...');
      const authHeaders = {};
      if (axiosInstance.defaults.headers.common['Authorization']) {
        authHeaders['Authorization'] = axiosInstance.defaults.headers.common['Authorization'];
        console.log('✅ getPrinters: Encabezado de autorización encontrado y aplicado');
      } else {
        console.log('⚠️ getPrinters: No se encontró encabezado de autorización');
      }
      
      // Crear una instancia especial de axios que no siga redirecciones automáticamente
      console.log('🛠️ getPrinters: Creando instancia personalizada de axios sin redirecciones automáticas...');
      const axiosNoRedirect = axios.create({
        maxRedirects: 0, // No seguir redirecciones automáticamente
        withCredentials: false,
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          ...authHeaders
        },
        validateStatus: function (status) {
          // Considerar 307 como válido para capturarlo
          return (status >= 200 && status < 300) || status === 307;
        }
      });
      
      console.log('✅ getPrinters: Instancia de axios configurada para manejar redirecciones manualmente');

      // Parámetros de consulta
      const params = agentId ? { agent_id: agentId } : {};
      if (agentId) {
        console.log(`🔍 getPrinters: Parámetros configurados: { agent_id: ${agentId} }`);
      } else {
        console.log('🔍 getPrinters: Sin parámetros de consulta adicionales');
      }
      
      console.log('🚀 getPrinters: Realizando solicitud inicial a https://copierconnectremote.com/api/v1/monitor/printers');
      
      try {
        // Primer intento - con URL absoluta HTTPS
        console.time('⏱️ getPrinters: Tiempo de solicitud inicial');
        const response = await axiosNoRedirect.get('https://copierconnectremote.com/api/v1/monitor/printers', { params });
        console.timeEnd('⏱️ getPrinters: Tiempo de solicitud inicial');
        
        console.log(`📌 getPrinters: Respuesta recibida con estado: ${response.status}`);
        console.log(`📌 getPrinters: Encabezados de respuesta: ${JSON.stringify(response.headers)}`);
        
        // Si es una redirección 307, extraer la URL de destino y forzar HTTPS
        if (response.status === 307 && response.headers.location) {
          let redirectUrl = response.headers.location;
          console.log(`🔄 getPrinters: Redirección 307 detectada a: ${redirectUrl}`);
          
          // Asegurarse de que la URL de redirección use HTTPS
          if (redirectUrl.startsWith('http://')) {
            const originalUrl = redirectUrl;
            redirectUrl = redirectUrl.replace('http://', 'https://');
            console.log(`🔒 getPrinters: URL de redirección convertida de ${originalUrl} a ${redirectUrl}`);
          } else {
            console.log(`🔍 getPrinters: La URL de redirección ya usa HTTPS o es relativa: ${redirectUrl}`);
          }
          
          // Si la URL es relativa, construir URL completa
          if (!redirectUrl.startsWith('http')) {
            const originalUrl = redirectUrl;
            const base = 'https://copierconnectremote.com';
            redirectUrl = redirectUrl.startsWith('/') 
              ? `${base}${redirectUrl}` 
              : `${base}/${redirectUrl}`;
            console.log(`🔗 getPrinters: URL relativa "${originalUrl}" convertida a absoluta: "${redirectUrl}"`);
          }
          
          console.log(`🚀 getPrinters: Siguiendo redirección manualmente a: ${redirectUrl}`);
          
          // Hacer una solicitud manual a la URL de redirección, pero con HTTPS forzado
          console.time('⏱️ getPrinters: Tiempo de solicitud a redirección');
          const redirectResponse = await axios.get(redirectUrl, { 
            params,
            headers: axiosNoRedirect.defaults.headers,
            // Desactivar seguimiento de redirecciones adicionales
            maxRedirects: 0,
            validateStatus: function (status) {
              return (status >= 200 && status < 300) || status === 307;
            }
          });
          console.timeEnd('⏱️ getPrinters: Tiempo de solicitud a redirección');
          
          console.log(`✅ getPrinters: Solicitud a URL de redirección exitosa, estado: ${redirectResponse.status}`);
          
          if (redirectResponse.status === 307) {
            console.log('⚠️ getPrinters: Se recibió otra redirección 307. Múltiples redirecciones no manejadas.');
          }
          
          // Verificar tipo de datos recibidos
          if (redirectResponse.data) {
            console.log(`📦 getPrinters: Datos recibidos. Tipo: ${typeof redirectResponse.data}`);
            if (Array.isArray(redirectResponse.data)) {
              console.log(`📊 getPrinters: Se recibieron ${redirectResponse.data.length} impresoras`);
            } else {
              console.log(`⚠️ getPrinters: Los datos recibidos no son un array: ${JSON.stringify(redirectResponse.data).substring(0, 100)}...`);
            }
          } else {
            console.log('⚠️ getPrinters: No se recibieron datos en la respuesta');
          }
          
          return redirectResponse.data || [];
        } else if (response.status >= 200 && response.status < 300) {
          console.log('✅ getPrinters: Solicitud exitosa sin redirección');
          
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
        } else {
          console.log(`⚠️ getPrinters: Se recibió un código de estado inesperado: ${response.status}`);
          return [];
        }
      } catch (redirectError) {
        console.error('❌ getPrinters: Error siguiendo redirección:', redirectError);
        console.log('📝 getPrinters: Detalles del error:', {
          message: redirectError.message,
          code: redirectError.code,
          status: redirectError.response?.status,
          stack: redirectError.stack
        });
        
        // Enfoque alternativo: probar con fetch API nativo que tiene más control sobre redirecciones
        console.log('🔄 getPrinters: Intentando con fetch API nativo...');
        
        // Construir URL con parámetros
        const queryParams = new URLSearchParams(params).toString();
        const urlWithParams = `https://copierconnectremote.com/api/v1/monitor/printers${queryParams ? `?${queryParams}` : ''}`;
        console.log(`🔗 getPrinters: URL construida para fetch: ${urlWithParams}`);
        
        try {
          console.time('⏱️ getPrinters: Tiempo de solicitud con fetch');
          const fetchResponse = await fetch(urlWithParams, {
            method: 'GET',
            headers: {
              'Accept': 'application/json',
              'Content-Type': 'application/json',
              ...authHeaders
            },
            redirect: 'manual' // No seguir redirecciones automáticamente
          });
          console.timeEnd('⏱️ getPrinters: Tiempo de solicitud con fetch');
          
          console.log(`📌 getPrinters: Respuesta fetch recibida. Estado: ${fetchResponse.status}, Tipo: ${fetchResponse.type}`);
          
          // Listar todos los encabezados recibidos
          console.log('📋 getPrinters: Encabezados de respuesta fetch:');
          fetchResponse.headers.forEach((value, key) => {
            console.log(`   ${key}: ${value}`);
          });
          
          if (fetchResponse.status === 307 || fetchResponse.type === 'opaqueredirect') {
            const redirectLocation = fetchResponse.headers.get('location');
            console.log(`🔄 getPrinters: Redirección detectada con fetch a: ${redirectLocation}`);
            
            if (redirectLocation) {
              // Asegurarse que la URL use HTTPS
              let secureRedirectUrl = redirectLocation;
              if (secureRedirectUrl.startsWith('http://')) {
                const originalUrl = secureRedirectUrl;
                secureRedirectUrl = secureRedirectUrl.replace('http://', 'https://');
                console.log(`🔒 getPrinters: URL de redirección fetch convertida de ${originalUrl} a ${secureRedirectUrl}`);
              }
              
              // Si es una URL relativa, construir URL completa
              if (!secureRedirectUrl.startsWith('http')) {
                const originalUrl = secureRedirectUrl;
                secureRedirectUrl = `https://copierconnectremote.com${secureRedirectUrl.startsWith('/') ? '' : '/'}${secureRedirectUrl}`;
                console.log(`🔗 getPrinters: URL relativa fetch "${originalUrl}" convertida a absoluta: "${secureRedirectUrl}"`);
              }
              
              console.log(`🚀 getPrinters: Siguiendo redirección con fetch a: ${secureRedirectUrl}`);
              
              try {
                console.time('⏱️ getPrinters: Tiempo de solicitud fetch a redirección');
                const finalResponse = await fetch(secureRedirectUrl, {
                  method: 'GET',
                  headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    ...authHeaders
                  }
                });
                console.timeEnd('⏱️ getPrinters: Tiempo de solicitud fetch a redirección');
                
                console.log(`📌 getPrinters: Respuesta final fetch. Estado: ${finalResponse.status}`);
                
                if (finalResponse.ok) {
                  const data = await finalResponse.json();
                  console.log(`✅ getPrinters: Datos obtenidos correctamente con fetch. Tipo: ${typeof data}`);
                  if (Array.isArray(data)) {
                    console.log(`📊 getPrinters: Se recibieron ${data.length} impresoras con fetch`);
                  }
                  return data || [];
                } else {
                  console.log(`❌ getPrinters: La respuesta final fetch no fue exitosa. Estado: ${finalResponse.status}`);
                  const errorText = await finalResponse.text();
                  console.log(`📝 getPrinters: Texto de error: ${errorText.substring(0, 200)}...`);
                }
              } catch (finalFetchError) {
                console.error('❌ getPrinters: Error en solicitud fetch final:', finalFetchError);
              }
            }
          } else if (fetchResponse.ok) {
            console.log('✅ getPrinters: Solicitud fetch exitosa sin redirección');
            const data = await fetchResponse.json();
            console.log(`📦 getPrinters: Datos obtenidos con fetch. Tipo: ${typeof data}`);
            if (Array.isArray(data)) {
              console.log(`📊 getPrinters: Se recibieron ${data.length} impresoras con fetch`);
            }
            return data || [];
          } else {
            console.log(`❌ getPrinters: La respuesta fetch no fue exitosa. Estado: ${fetchResponse.status}`);
            try {
              const errorText = await fetchResponse.text();
              console.log(`📝 getPrinters: Texto de error: ${errorText.substring(0, 200)}...`);
            } catch (textError) {
              console.log('❌ getPrinters: No se pudo obtener el texto de error');
            }
          }
        } catch (fetchError) {
          console.error('❌ getPrinters: Error usando fetch API:', fetchError);
        }
        
        // Último enfoque: usar XMLHttpRequest directamente
        console.log('🔄 getPrinters: Intentando con XMLHttpRequest directamente...');
        
        try {
          const xhr = new XMLHttpRequest();
          xhr.open('GET', 'https://copierconnectremote.com/api/v1/monitor/printers', false); // Síncrono para este ejemplo
          
          // Agregar encabezados
          xhr.setRequestHeader('Accept', 'application/json');
          xhr.setRequestHeader('Content-Type', 'application/json');
          if (authHeaders['Authorization']) {
            xhr.setRequestHeader('Authorization', authHeaders['Authorization']);
          }
          
          // No seguir redirecciones
          xhr.addEventListener('readystatechange', function() {
            if (xhr.readyState === 4) {
              console.log(`📌 getPrinters: XMLHttpRequest estado: ${xhr.status}`);
              if (xhr.status === 307) {
                console.log(`🔄 getPrinters: Redirección 307 detectada en XMLHttpRequest`);
                const location = xhr.getResponseHeader('Location');
                console.log(`📍 getPrinters: URL de redirección: ${location}`);
              }
            }
          });
          
          xhr.send();
          
          console.log(`📌 getPrinters: Resultado final de XMLHttpRequest: estado ${xhr.status}, texto: ${xhr.statusText}`);
        } catch (xhrError) {
          console.error('❌ getPrinters: Error usando XMLHttpRequest:', xhrError);
        }
        
        // Si todos los métodos fallan, lanzar el error original
        console.log('❌ getPrinters: Todos los métodos alternativos fallaron. Lanzando error original.');
        throw redirectError;
      }
    } catch (error) {
      console.error("❌ getPrinters: Error principal al obtener impresoras:", error);
      console.log('📝 getPrinters: Detalles del error principal:', {
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