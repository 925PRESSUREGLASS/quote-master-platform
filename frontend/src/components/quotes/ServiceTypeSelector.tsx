import React, { useEffect, useState } from 'react';

export interface ServiceOption {
  id: string;
  name: string;
  basePrice: number;
}

interface ServiceTypeSelectorProps {
  services: ServiceOption[];
  initialSelected?: string[];
  onChange?: (selected: string[], basePrice: number) => void;
}

export const ServiceTypeSelector: React.FC<ServiceTypeSelectorProps> = ({
  services,
  initialSelected = [],
  onChange
}) => {
  const [selected, setSelected] = useState<string[]>(initialSelected);

  // Notify parent of initial state
  useEffect(() => {
    const initialPrice = services
      .filter(service => initialSelected.includes(service.id))
      .reduce((sum, service) => sum + service.basePrice, 0);
    onChange?.(initialSelected, initialPrice);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const toggleService = (id: string) => {
    setSelected(prev => {
      const updated = prev.includes(id)
        ? prev.filter(s => s !== id)
        : [...prev, id];
      const newPrice = services
        .filter(service => updated.includes(service.id))
        .reduce((sum, service) => sum + service.basePrice, 0);
      onChange?.(updated, newPrice);
      return updated;
    });
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {services.map(service => (
        <div
          key={service.id}
          className={`p-4 rounded-lg border cursor-pointer transition-colors ${
            selected.includes(service.id)
              ? 'bg-blue-50 border-blue-200'
              : 'bg-white border-gray-200 hover:border-blue-200'
          }`}
          onClick={() => toggleService(service.id)}
        >
          <div className="flex items-center justify-between">
            <span className="font-medium text-gray-900">{service.name}</span>
            <span className="text-sm text-gray-600">${service.basePrice}</span>
          </div>
        </div>
      ))}
    </div>
  );
};

