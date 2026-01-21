import { useState } from "react";
import { X } from "lucide-react";
import "../styles/size-chart.css";

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
      className="size-chart-overlay"
      id="size-chart-overlay"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      data-testid="size-chart-modal-overlay"
    >
      <div className="size-chart-modal" id="size-chart-modal">
        <div className="size-chart-tabs" id="size-chart-tabs">
          <button
            onClick={() => setActiveTab("chart")}
            className={`size-chart-tab ${activeTab === "chart" ? 'size-chart-tab--active' : ''}`}
            id="size-chart-tab-chart"
            data-testid="tab-size-chart"
          >
            Size Chart
          </button>
          <button
            onClick={() => setActiveTab("measure")}
            className={`size-chart-tab ${activeTab === "measure" ? 'size-chart-tab--active' : ''}`}
            id="size-chart-tab-measure"
            data-testid="tab-how-to-measure"
          >
            How to measure
          </button>
          <button 
            onClick={onClose}
            className="size-chart-close-btn"
            id="size-chart-close-btn"
            data-testid="btn-close-size-chart"
          >
            <X className="size-chart-close-icon" />
          </button>
        </div>
        
        {activeTab === "chart" ? (
          <div className="size-chart-content" id="size-chart-content">
            <div className="size-chart-unit-toggle-wrapper">
              <div className="size-chart-unit-toggle" id="size-chart-unit-toggle">
                <button
                  onClick={() => setUnit("in")}
                  className={`size-chart-unit-btn ${unit === "in" ? 'size-chart-unit-btn--active' : ''}`}
                  id="size-chart-unit-in"
                  data-testid="btn-unit-in"
                >
                  in
                </button>
                <button
                  onClick={() => setUnit("cm")}
                  className={`size-chart-unit-btn ${unit === "cm" ? 'size-chart-unit-btn--active' : ''}`}
                  id="size-chart-unit-cm"
                  data-testid="btn-unit-cm"
                >
                  cm
                </button>
              </div>
            </div>
            
            <table className="size-chart-table" id="size-chart-table">
              <thead>
                <tr>
                  <th></th>
                  <th>Size</th>
                  <th>Chest</th>
                  <th>Front</th>
                  <th>Shoulder</th>
                  <th>Sleeve</th>
                </tr>
              </thead>
              <tbody>
                {sizeData.map((row) => (
                  <tr 
                    key={row.size} 
                    className={selectedSize === row.size ? 'size-chart-row--selected' : ''}
                  >
                    <td>
                      <div 
                        onClick={() => onSelectSize(row.size)}
                        className={`size-chart-radio ${selectedSize === row.size ? 'size-chart-radio--selected' : ''}`}
                        id={`size-chart-radio-${row.size}`}
                      >
                        {selectedSize === row.size && (
                          <div className="size-chart-radio-dot" />
                        )}
                      </div>
                    </td>
                    <td className="size-chart-size-label">{row.size}</td>
                    <td>{row.chest[unit]}</td>
                    <td>{row.front[unit]}</td>
                    <td>{row.shoulder[unit]}</td>
                    <td>{row.sleeve[unit]}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="size-chart-content" id="size-chart-measure-content">
            <div className="size-chart-measure-content">
              <div className="size-chart-measure-item">
                <h4 className="size-chart-measure-title">Chest</h4>
                <p className="size-chart-measure-text">Measure around the fullest part of your chest, keeping the tape horizontal.</p>
              </div>
              <div className="size-chart-measure-item">
                <h4 className="size-chart-measure-title">Front Length</h4>
                <p className="size-chart-measure-text">Measure from the highest point of your shoulder to the desired length.</p>
              </div>
              <div className="size-chart-measure-item">
                <h4 className="size-chart-measure-title">Across Shoulder</h4>
                <p className="size-chart-measure-text">Measure from the edge of one shoulder to the edge of the other shoulder.</p>
              </div>
              <div className="size-chart-measure-item">
                <h4 className="size-chart-measure-title">Sleeve Length</h4>
                <p className="size-chart-measure-text">Measure from the shoulder seam to the end of the sleeve.</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
