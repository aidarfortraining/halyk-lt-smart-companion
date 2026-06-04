import { ChatColumn } from './components/ChatColumn'
import { TravelPlan } from './components/TravelPlan'
import { TripProvider } from './state/trip'
import './styles/companion.css'

export default function App() {
  return (
    <TripProvider>
      <div id="v2wrap">
        <div className="app">
          <ChatColumn />
          <TravelPlan />
        </div>
      </div>
    </TripProvider>
  )
}
