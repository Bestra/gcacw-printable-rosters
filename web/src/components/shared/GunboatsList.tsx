import type { Gunboat } from "../../types";
import "./GunboatsList.css";

interface GunboatsListProps {
  gunboats: Gunboat[];
  className?: string;
}

export function GunboatsList({ gunboats, className = "" }: GunboatsListProps) {
  if (gunboats.length === 0) return null;
  
  return (
    <div className={`gunboats-list ${className}`}>
      <h4 className="gunboats-list__title">Gunboats</h4>
      <ul className="gunboats-list__items">
        {gunboats.map((gunboat, index) => (
          <li key={index} className="gunboats-list__item">
            <span className="gunboats-list__name">{gunboat.name}</span>
            {gunboat.location && (
              <span className="gunboats-list__location"> — {gunboat.location}</span>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
