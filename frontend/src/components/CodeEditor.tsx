/**
 * Monaco Code Editor Component with Real-Time Analysis
 *
 * Features:
 * - Monaco editor with Python syntax highlighting
 * - Real-time diagnostic markers from WebSocket
 * - Hover provider for error details
 * - Configurable themes (VS Dark/Light)
 * - Keyboard shortcuts and auto-completion
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';
import Editor, { OnMount, OnChange } from '@monaco-editor/react';
import * as monaco from 'monaco-editor';

import { useAnalysisStore } from '../stores/analysisStore';
import { Diagnostic } from '../types/analysis';

interface CodeEditorProps {
  initialCode?: string;
  language?: string;
  theme?: 'vs-dark' | 'vs-light';
  height?: string;
  onCodeChange?: (code: string) => void;
  readOnly?: boolean;
}

export const CodeEditor: React.FC<CodeEditorProps> = ({
  initialCode = '',
  language = 'python',
  theme = 'vs-dark',
  height = '400px',
  onCodeChange,
  readOnly = false,
}) => {
  const editorRef = useRef<monaco.editor.IStandaloneCodeEditor | null>(null);
  const markersRef = useRef<string[]>([]);

  const {
    diagnostics,
    sendCodeUpdate,
    connectionStatus,
    lastAnalysisTime
  } = useAnalysisStore();

  const [code, setCode] = useState(initialCode);

  // Handle editor mounting
  const handleEditorDidMount: OnMount = useCallback((editor, monaco) => {
    editorRef.current = editor;

    // Configure editor options
    editor.updateOptions({
      fontSize: 14,
      fontFamily: "'JetBrains Mono', 'Monaco', 'Menlo', monospace",
      lineNumbers: 'on',
      minimap: { enabled: true },
      scrollBeyondLastLine: false,
      wordWrap: 'on',
      automaticLayout: true,
      tabSize: 4,
      insertSpaces: true,
      detectIndentation: false,
      renderWhitespace: 'boundary',
      bracketPairColorization: { enabled: true },
      guides: {
        indentation: true,
        bracketPairs: true,
      },
    });

    // Add keyboard shortcuts
    editor.addAction({
      id: 'manual-analysis',
      label: 'Run Analysis',
      keybindings: [monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS],
      run: () => {
        const currentCode = editor.getValue();
        sendCodeUpdate(currentCode, language);
      },
    });

    // Setup hover provider for diagnostics
    monaco.languages.registerHoverProvider(language, {
      provideHover: (model, position) => {
        const line = position.lineNumber;
        const column = position.column;

        // Find diagnostic at this position
        const diagnostic = diagnostics.find(d =>
          d.line === line &&
          d.column <= column &&
          (d.end_column == null || column <= d.end_column)
        );

        if (diagnostic) {
          const severityText = diagnostic.severity.toUpperCase();
          const codeText = diagnostic.code ? ` (${diagnostic.code})` : '';
          const fixText = diagnostic.fix_suggestion
            ? `\n\n**Suggestion:** ${diagnostic.fix_suggestion}`
            : '';

          return {
            range: new monaco.Range(
              line,
              diagnostic.column + 1,
              diagnostic.end_line || line,
              (diagnostic.end_column || diagnostic.column) + 1
            ),
            contents: [
              {
                value: `**${severityText}**${codeText}: ${diagnostic.message}${fixText}`,
                supportHtml: false,
              },
            ],
          };
        }

        return null;
      },
    });

    // Initial code analysis if we have code
    if (code.trim()) {
      sendCodeUpdate(code, language);
    }
  }, [diagnostics, sendCodeUpdate, language, code]);

  // Handle code changes
  const handleCodeChange: OnChange = useCallback((value) => {
    const newCode = value || '';
    setCode(newCode);
    onCodeChange?.(newCode);

    // Debounced analysis update
    const timeoutId = setTimeout(() => {
      if (newCode.trim() !== code.trim()) {
        sendCodeUpdate(newCode, language);
      }
    }, 500); // 500ms debounce

    return () => clearTimeout(timeoutId);
  }, [code, sendCodeUpdate, language, onCodeChange]);

  // Update diagnostics in Monaco
  useEffect(() => {
    if (!editorRef.current || !diagnostics) return;

    const model = editorRef.current.getModel();
    if (!model) return;

    // Clear existing markers
    monaco.editor.removeAllMarkers('realtime-analysis');

    // Convert diagnostics to Monaco markers
    const markers: monaco.editor.IMarkerData[] = diagnostics.map(diagnostic => ({
      startLineNumber: diagnostic.line,
      startColumn: diagnostic.column + 1, // Monaco is 1-indexed
      endLineNumber: diagnostic.end_line || diagnostic.line,
      endColumn: (diagnostic.end_column || diagnostic.column) + 1,
      message: diagnostic.message,
      severity: getSeverity(diagnostic.severity),
      source: diagnostic.source,
      code: diagnostic.code || undefined,
    }));

    // Set markers on the model
    monaco.editor.setModelMarkers(model, 'realtime-analysis', markers);

  }, [diagnostics]);

  // Helper function to convert diagnostic severity to Monaco severity
  const getSeverity = (severity: string): monaco.MarkerSeverity => {
    switch (severity) {
      case 'error':
        return monaco.MarkerSeverity.Error;
      case 'warning':
        return monaco.MarkerSeverity.Warning;
      case 'info':
        return monaco.MarkerSeverity.Info;
      case 'hint':
        return monaco.MarkerSeverity.Hint;
      default:
        return monaco.MarkerSeverity.Info;
    }
  };

  return (
    <div className="relative">
      {/* Connection status indicator */}
      <div className="absolute top-2 right-2 z-10 flex items-center space-x-2">
        <ConnectionStatusIndicator status={connectionStatus} />
        {lastAnalysisTime && (
          <div className="text-xs bg-gray-800 text-white px-2 py-1 rounded">
            {lastAnalysisTime}ms
          </div>
        )}
      </div>

      <Editor
        height={height}
        language={language}
        theme={theme}
        value={code}
        onChange={handleCodeChange}
        onMount={handleEditorDidMount}
        options={{
          readOnly,
          scrollBeyondLastLine: false,
          wordWrap: 'on',
          minimap: { enabled: true },
          automaticLayout: true,
        }}
      />
    </div>
  );
};

// Connection status indicator component
interface ConnectionStatusIndicatorProps {
  status: 'connecting' | 'connected' | 'disconnected' | 'error';
}

const ConnectionStatusIndicator: React.FC<ConnectionStatusIndicatorProps> = ({ status }) => {
  const getStatusDisplay = () => {
    switch (status) {
      case 'connecting':
        return { color: 'bg-yellow-500', text: 'Connecting...', pulse: true };
      case 'connected':
        return { color: 'bg-green-500', text: 'Connected', pulse: false };
      case 'disconnected':
        return { color: 'bg-gray-500', text: 'Disconnected', pulse: false };
      case 'error':
        return { color: 'bg-red-500', text: 'Error', pulse: true };
      default:
        return { color: 'bg-gray-500', text: 'Unknown', pulse: false };
    }
  };

  const { color, text, pulse } = getStatusDisplay();

  return (
    <div className="flex items-center space-x-1 text-xs bg-gray-800 text-white px-2 py-1 rounded">
      <div
        className={`w-2 h-2 rounded-full ${color} ${pulse ? 'animate-pulse' : ''}`}
      />
      <span>{text}</span>
    </div>
  );
};

export default CodeEditor;