import React from 'react';
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Printer, Download, Users, BookOpen, ArrowRight } from 'lucide-react';

const Home = () => {
  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-16">
        <div className="text-center max-w-3xl mx-auto">
          <h1 className="text-4xl font-bold text-gray-900 mb-6">
            Sistema de Monitoreo de Impresoras Inteligente
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Gestiona, monitorea y optimiza tu flota de impresoras desde una única plataforma centralizada
          </p>
          <div className="flex gap-4 justify-center">
            <Button className="bg-blue-600 hover:bg-blue-700">
              Comenzar ahora
            </Button>
            <Button variant="outline">
              Saber más
            </Button>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="container mx-auto px-4 py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card className="bg-white">
            <CardHeader>
              <Printer className="h-8 w-8 text-blue-600 mb-2" />
              <CardTitle>Monitoreo en Tiempo Real</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">
                Supervisa el estado de tus impresoras en tiempo real, niveles de tinta y estado operativo
              </p>
            </CardContent>
          </Card>

          <Card className="bg-white">
            <CardHeader>
              <Download className="h-8 w-8 text-blue-600 mb-2" />
              <CardTitle>Gestión de Firmware</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">
                Descarga y actualiza firmware fácilmente con nuestro sistema centralizado
              </p>
            </CardContent>
          </Card>

          <Card className="bg-white">
            <CardHeader>
              <Users className="h-8 w-8 text-blue-600 mb-2" />
              <CardTitle>Comunidad Activa</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">
                Participa en nuestro foro y comparte experiencias con otros usuarios
              </p>
            </CardContent>
          </Card>

          <Card className="bg-white">
            <CardHeader>
              <BookOpen className="h-8 w-8 text-blue-600 mb-2" />
              <CardTitle>Documentación Completa</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">
                Accede a manuales detallados y guías de solución de problemas
              </p>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* CTA Section */}
      <div className="container mx-auto px-4 py-16">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            ¿Listo para empezar?
          </h2>
          <p className="text-xl text-gray-600 mb-8">
            Únete a nuestra plataforma y optimiza la gestión de tus impresoras
          </p>
          <Button className="bg-blue-600 hover:bg-blue-700">
            Crear cuenta gratuita <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
};

export default Home;