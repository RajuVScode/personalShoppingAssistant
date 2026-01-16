import { useState } from "react";
import { X } from "lucide-react";

interface SizeChartModalProps {
  isOpen: boolean;
  onClose: () => void;
  selectedSize: string | null;
  onSelectSize: (size: string) => void;
}

const sizeData = [
  { size: 'S', chest: { in: 41.0, cm: 104.1 }, front: { in: 28.5, cm: 72.4 }, shoulder: { in: 21.0, cm: 53.3 }, sleeve: { in: 10.5, cm: 26.7 } },
  { size: 'M', chest: { in: 43.0, cm: 109.2 }, front: { in: 29.0, cm: 73.7 }, shoulder: { in: 22.0, cm: 55.9 }, sleeve: { in: 10.8, cm: 27.4 } },
  { size: 'L', chest: { in: 45.0, cm: 114.3 }, front: { in: 30.0, cm: 76.2 }, shoulder: { in: 23.0, cm: 58.4 }, sleeve: { in: 11.0, cm: 27.9 } },
  { size: 'XL', chest: { in: 47.0, cm: 119.4 }, front: { in: 30.5, cm: 77.5 }, shoulder: { in: 24.0, cm: 61.0 }, sleeve: { in: 11.3, cm: 28.7 } },
  { size: 'XXL', chest: { in: 49.0, cm: 124.5 }, front: { in: 31.0, cm: 78.7 }, shoulder: { in: 25.0, cm: 63.5 }, sleeve: { in: 11.5, cm: 29.2 } },
];

export function SizeChartModal({ isOpen, onClose, selectedSize, onSelectSize }: SizeChartModalProps) {
  const [activeTab, setActiveTab] = useState<"chart" | "measure">("chart");
  const [unit, setUnit] = useState<"in" | "cm">("in");

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 z-[70] flex items-center justify-center bg-black/50"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      data-testid="size-chart-modal-overlay"
    >
      <div className="bg-white w-[600px] h-[500px] rounded-lg shadow-2xl flex flex-col overflow-hidden">
        <div className="flex border-b">
          <button
            onClick={() => setActiveTab("chart")}
            className={`flex-1 py-2.5 text-center text-sm font-semibold transition-colors ${
              activeTab === "chart" 
                ? 'text-pink-500 border-b-2 border-pink-500' 
                : 'text-gray-500 hover:text-gray-700'
            }`}
            data-testid="tab-size-chart"
          >
            Size Chart
          </button>
          <button
            onClick={() => setActiveTab("measure")}
            className={`flex-1 py-2.5 text-center text-sm font-semibold transition-colors ${
              activeTab === "measure" 
                ? 'text-pink-500 border-b-2 border-pink-500' 
                : 'text-gray-500 hover:text-gray-700'
            }`}
            data-testid="tab-how-to-measure"
          >
            How to measure
          </button>
          <button 
            onClick={onClose}
            className="px-3 text-gray-400 hover:text-gray-600"
            data-testid="btn-close-size-chart"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
        
        {activeTab === "chart" ? (
          <div className="p-6 flex-1 overflow-auto">
            <div className="flex justify-end mb-4">
              <div className="flex items-center bg-gray-100 rounded-full p-1">
                <button
                  onClick={() => setUnit("in")}
                  className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
                    unit === "in" 
                      ? 'bg-gray-800 text-white' 
                      : 'text-gray-600 hover:text-gray-800'
                  }`}
                  data-testid="btn-unit-in"
                >
                  in
                </button>
                <button
                  onClick={() => setUnit("cm")}
                  className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
                    unit === "cm" 
                      ? 'bg-gray-800 text-white' 
                      : 'text-gray-600 hover:text-gray-800'
                  }`}
                  data-testid="btn-unit-cm"
                >
                  cm
                </button>
              </div>
            </div>
            
            <table className="w-full">
              <thead>
                <tr className="text-gray-600 text-sm">
                  <th className="py-3 text-left font-medium w-12"></th>
                  <th className="py-3 text-left font-medium">Size</th>
                  <th className="py-3 text-center font-medium">Chest ({unit})</th>
                  <th className="py-3 text-center font-medium">Front Length ({unit})</th>
                  <th className="py-3 text-center font-medium">Across Shoulder ({unit})</th>
                  <th className="py-3 text-center font-medium">Sleeve-Length ({unit})</th>
                </tr>
              </thead>
              <tbody>
                {sizeData.map((row) => (
                  <tr 
                    key={row.size} 
                    className={`border-t ${selectedSize === row.size ? 'font-bold' : ''}`}
                  >
                    <td className="py-4">
                      <div 
                        onClick={() => onSelectSize(row.size)}
                        className={`w-5 h-5 rounded-full border-2 cursor-pointer flex items-center justify-center ${
                          selectedSize === row.size 
                            ? 'border-pink-500' 
                            : 'border-gray-300'
                        }`}
                      >
                        {selectedSize === row.size && (
                          <div className="w-2.5 h-2.5 rounded-full bg-pink-500" />
                        )}
                      </div>
                    </td>
                    <td className="py-4 font-medium">{row.size}</td>
                    <td className="py-4 text-center">{row.chest[unit]}</td>
                    <td className="py-4 text-center">{row.front[unit]}</td>
                    <td className="py-4 text-center">{row.shoulder[unit]}</td>
                    <td className="py-4 text-center">{row.sleeve[unit]}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-6 flex-1 overflow-auto">
            <div className="space-y-4 text-gray-600">
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">Chest</h4>
                <p className="text-sm">Measure around the fullest part of your chest, keeping the tape horizontal.</p>
              </div>
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">Front Length</h4>
                <p className="text-sm">Measure from the highest point of your shoulder to the desired length.</p>
              </div>
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">Across Shoulder</h4>
                <p className="text-sm">Measure from the edge of one shoulder to the edge of the other shoulder.</p>
              </div>
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">Sleeve Length</h4>
                <p className="text-sm">Measure from the shoulder seam to the end of the sleeve.</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
