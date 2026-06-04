import { useTrip } from '../state/trip'

export function EmergencyBlock() {
  const { snapshot } = useTrip()
  if (!snapshot || snapshot.emergency.length === 0) return null
  return (
    <div className="emergency">
      <div className="emg-ttl">🆘 Экстренная помощь</div>
      {snapshot.emergency.map((e, i) => (
        <div key={i} className="emg-row">
          <span className="emg-l">{e.label}</span>
          <span className="emg-v">{e.value}</span>
        </div>
      ))}
    </div>
  )
}
