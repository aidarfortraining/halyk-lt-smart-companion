import { useState } from 'react'
import { ChatColumn } from './components/ChatColumn'
import { TravelPlan } from './components/TravelPlan'
import { Wizard } from './components/wizard/Wizard'
import { TripProvider } from './state/trip'
import './styles/companion.css'

const PURCHASED_KEY = 'halyk_purchased'

export default function App() {
  // Ticket purchase (wizard) gates the companion. The flag persists so a page refresh
  // resumes the companion instead of replaying the wizard; the ↻ reset clears it.
  const [purchased, setPurchased] = useState(() => localStorage.getItem(PURCHASED_KEY) === '1')

  if (!purchased) {
    return <Wizard onBuy={() => { localStorage.setItem(PURCHASED_KEY, '1'); setPurchased(true) }} />
  }

  return (
    <TripProvider>
      <div id="v2wrap">
        <div className="app">
          <ChatColumn onExitToWizard={() => { localStorage.removeItem(PURCHASED_KEY); setPurchased(false) }} />
          <TravelPlan />
        </div>
      </div>
    </TripProvider>
  )
}
