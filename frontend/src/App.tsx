import { StreamPanel } from "./components/stream-panel"
import { DetectionList } from "./components/detection-list"
import { Bird } from "lucide-react"
import { ThemeProvider } from "@/components/theme-provider"
import { ModeToggle } from "@/components/mode-toggle"

function App() {
  return (
    <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
      <div className="h-screen w-screen bg-background text-foreground flex flex-col overflow-hidden">
        <header className="h-16 border-b border-border flex items-center px-6 bg-card/30 backdrop-blur shrink-0">
          <h1 className="text-2xl font-bold text-primary flex items-center gap-2">
            <Bird className="w-8 h-8 text-accent" />
            BirdyBird
          </h1>
          <div className="ml-auto">
            <ModeToggle />
          </div>
        </header>

        <main className="flex-1 p-4 grid grid-cols-1 md:grid-cols-3 gap-4 overflow-hidden">
          <div className="md:col-span-2 h-full min-h-0">
            <StreamPanel />
          </div>
          <div className="md:col-span-1 h-full min-h-0">
            <DetectionList />
          </div>
        </main>
      </div>
    </ThemeProvider>
  )
}

export default App
