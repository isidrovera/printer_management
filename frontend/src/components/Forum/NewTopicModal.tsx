import React, { useState } from 'react';
import { X, Upload, Paperclip } from 'lucide-react';
import { Button } from '../ui/button';

interface NewTopicModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const NewTopicModal = ({ isOpen, onClose }: NewTopicModalProps) => {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [tags, setTags] = useState('');
  const [files, setFiles] = useState<FileList | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log({ title, content, tags, files });
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div className="bg-white rounded-lg w-full max-w-4xl my-8">
        <div className="sticky top-0 bg-white z-10 flex justify-between items-center p-6 border-b">
          <h2 className="text-2xl font-bold">Crear Nuevo Tema</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <X className="h-6 w-6" />
          </button>
        </div>

        <div className="max-h-[calc(100vh-200px)] overflow-y-auto">
          <form onSubmit={handleSubmit} className="p-6">
            <div className="space-y-6">
              {/* Título */}
              <div>
                <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
                  Título
                </label>
                <input
                  type="text"
                  id="title"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Escribe un título descriptivo"
                  required
                />
              </div>

              {/* Contenido */}
              <div>
                <label htmlFor="content" className="block text-sm font-medium text-gray-700 mb-2">
                  Contenido
                </label>
                <textarea
                  id="content"
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  rows={8}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Describe el problema o tema en detalle"
                  required
                />
              </div>

              {/* Tags */}
              <div>
                <label htmlFor="tags" className="block text-sm font-medium text-gray-700 mb-2">
                  Etiquetas (separadas por comas)
                </label>
                <input
                  type="text"
                  id="tags"
                  value={tags}
                  onChange={(e) => setTags(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="ej: HP, Firmware, Error"
                />
              </div>

              {/* Subida de archivos */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Archivos adjuntos
                </label>
                <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
                  <div className="space-y-1 text-center">
                    <Upload className="mx-auto h-12 w-12 text-gray-400" />
                    <div className="flex text-sm text-gray-600">
                      <label htmlFor="file-upload" className="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500">
                        <span>Sube un archivo</span>
                        <input
                          id="file-upload"
                          type="file"
                          className="sr-only"
                          multiple
                          onChange={(e) => setFiles(e.target.files)}
                          accept=".png,.jpg,.gif"
                        />
                      </label>
                      <p className="pl-1">o arrastra y suelta</p>
                    </div>
                    <p className="text-xs text-gray-500">
                      PNG, JPG, GIF hasta 10MB
                    </p>
                  </div>
                </div>
                {files && Array.from(files).map((file, index) => (
                  <div key={index} className="flex items-center mt-2">
                    <Paperclip className="h-4 w-4 text-gray-400 mr-2" />
                    <span className="text-sm text-gray-500">{file.name}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-6 flex justify-end space-x-3">
              <Button 
                type="button" 
                variant="outline"
                onClick={onClose}
              >
                Cancelar
              </Button>
              <Button type="submit">
                Crear Tema
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default NewTopicModal;