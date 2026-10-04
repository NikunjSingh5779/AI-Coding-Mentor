import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { Badge } from '@/components/ui/badge'
import { EditorPane } from '@/features/editor/EditorPane'
import { MentorPanel } from '@/features/mentor/MentorPanel'
import { RunPanel } from '@/features/run/RunPanel'
import { ProblemPanel } from '@/features/problems/ProblemPanel'
import { useSession } from '@/store/session'
import { Play, Square, Settings, History, TrendingUp } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function WorkspaceRoute() {
  const {
    currentSnapshot,
    diagnostics,
    isConnected,
    runResult,
    isRunning
  } = useSession()

  const [showProblems, setShowProblems] = useState(false)

  return (
    <div className="flex h-screen bg-background">
      {/* Navigation sidebar */}
      <div className="w-64 border-r bg-muted/50 p-4 flex flex-col">
        <div className="flex items-center gap-2 mb-6">
          <div className="w-8 h-8 bg-primary rounded-md flex items-center justify-center">
            <span className="text-primary-foreground font-bold text-sm">CM</span>
          </div>
          <div>
            <h1 className="font-semibold text-sm">Coding Mentor</h1>
            <p className="text-xs text-muted-foreground">Real-time analysis</p>
          </div>
        </div>

        {/* Connection status */}
        <div className="mb-4">
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-xs text-muted-foreground">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>

        <Separator className="mb-4" />

        {/* Navigation links */}
        <nav className="space-y-2 flex-1">
          <Button variant="secondary" className="w-full justify-start" asChild>
            <Link to="/workspace">
              <Play className="w-4 h-4 mr-2" />
              Workspace
            </Link>
          </Button>

          <Button variant="ghost" className="w-full justify-start" asChild>
            <Link to="/history">
              <History className="w-4 h-4 mr-2" />
              History
            </Link>
          </Button>

          <Button variant="ghost" className="w-full justify-start" asChild>
            <Link to="/progress">
              <TrendingUp className="w-4 h-4 mr-2" />
              Progress
            </Link>
          </Button>

          <Button variant="ghost" className="w-full justify-start" asChild>
            <Link to="/settings">
              <Settings className="w-4 h-4 mr-2" />
              Settings
            </Link>
          </Button>
        </nav>

        {/* Problems toggle */}
        <div className="mt-4">
          <Button
            variant="outline"
            size="sm"
            className="w-full"
            onClick={() => setShowProblems(!showProblems)}
          >
            {showProblems ? 'Hide' : 'Show'} Problems
          </Button>
        </div>
      </div>

      {/* Main content area */}
      <div className="flex-1 flex flex-col">
        {/* Top toolbar */}
        <div className="border-b p-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h2 className="font-semibold">Code Editor</h2>
            {diagnostics.length > 0 && (
              <Badge variant="destructive" className="text-xs">
                {diagnostics.length} issues
              </Badge>
            )}
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant={isRunning ? "destructive" : "default"}
              size="sm"
              disabled={!currentSnapshot?.code.trim()}
            >
              {isRunning ? (
                <>
                  <Square className="w-4 h-4 mr-2" />
                  Stop
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 mr-2" />
                  Run
                </>
              )}
            </Button>
          </div>
        </div>

        {/* Main workspace grid */}
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-4 p-4">
          {/* Left column - Editor and Run */}
          <div className="lg:col-span-2 space-y-4">
            {/* Problems panel (conditional) */}
            {showProblems && (
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">Practice Problems</CardTitle>
                </CardHeader>
                <CardContent>
                  <ProblemPanel />
                </CardContent>
              </Card>
            )}

            {/* Code editor */}
            <Card className="flex-1">
              <CardHeader className="pb-3">
                <CardTitle className="text-base">Code Editor</CardTitle>
              </CardHeader>
              <CardContent>
                <EditorPane />
              </CardContent>
            </Card>

            {/* Run panel */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">Output</CardTitle>
              </CardHeader>
              <CardContent>
                <RunPanel />
              </CardContent>
            </Card>
          </div>

          {/* Right column - Mentor */}
          <div className="space-y-4">
            <Card className="flex-1">
              <CardHeader className="pb-3">
                <CardTitle className="text-base">AI Mentor</CardTitle>
              </CardHeader>
              <CardContent>
                <MentorPanel />
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}