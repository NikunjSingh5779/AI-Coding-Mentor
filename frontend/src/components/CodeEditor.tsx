import React, { useCallback, useEffect, useRef, useState } from 'react';
import Editor, { OnChange, OnMount } from '@monaco-editor/react';
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

const toMarkerSeverity = (severity: Diagnostic['severity']): monaco.MarkerSeverity => {
  switch (severity) {
    case 'error':
      return monaco.MarkerSeverity.Error;
    case 'warning':
      return monaco.MarkerSeverity.Warning;
    case 'hint':
      return monaco.MarkerSeverity.Hint;
    default:
      return monaco.MarkerSeverity.Info;
  }
};

export const CodeEditor: React.FC<CodeEditorProps> = ({
  initialCode = '',
  language = 'python',
  theme = 'vs-dark',
  height = '400px',
  onCodeChange,
  readOnly = false,
}) => {
  const editorRef = useRef<monaco.editor.IStandaloneCodeEditor | null>(null);
  const hoverDisposableRef = useRef<monaco.IDisposable | null>(null);
  const diagnosticsRef = useRef<Diagnostic[]>([]);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const codeRef = useRef(initialCode);
  const { diagnostics, sendCodeUpdate, connectionStatus, lastAnalysisTime } =
    useAnalysisStore();
  const [code, setCode] = useState(initialCode);

  diagnosticsRef.current = diagnostics;
  codeRef.current = code;

  const handleEditorDidMount: OnMount = useCallback(
    (editor, monacoInstance) => {
      editorRef.current = editor;

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
        guides: { indentation: true, bracketPairs: true },
      });

      editor.addAction({
        id: 'manual-analysis',
        label: 'Run Analysis',
        keybindings: [monacoInstance.KeyMod.CtrlCmd | monacoInstance.KeyCode.KeyS],
        run: () => sendCodeUpdate(editor.getValue(), language),
      });

      hoverDisposableRef.current?.dispose();
      hoverDisposableRef.current = monacoInstance.languages.registerHoverProvider(language, {
        provideHover: (_model, position) => {
          const diagnostic = diagnosticsRef.current.find((item) => {
            if (item.line !== position.lineNumber) return false;
            const start = item.column + 1;
            const end = (item.end_column ?? item.column) + 1;
            return position.column >= start && position.column <= Math.max(start, end);
          });

          if (!diagnostic) return null;

          return {
            range: new monacoInstance.Range(
              diagnostic.line,
              diagnostic.column + 1,
              diagnostic.end_line ?? diagnostic.line,
              (diagnostic.end_column ?? diagnostic.column + 1) + 1,
            ),
            contents: [
              {
                value:
                  `**${diagnostic.severity.toUpperCase()}**${diagnostic.code ? ` (${diagnostic.code})` : ''}: ${diagnostic.message}${diagnostic.fix_suggestion ? `\\n\\n**Suggestion:** ${diagnostic.fix_suggestion}` : ''}`,
              },
            ],
          };
        },
      });

      return undefined;
    },
    [language, sendCodeUpdate],
  );

  const handleCodeChange: OnChange = useCallback(
    (value) => {
      const newCode = value ?? '';
      setCode(newCode);
      codeRef.current = newCode;
      onCodeChange?.(newCode);

      if (debounceRef.current) clearTimeout(debounceRef.current);

      if (!newCode.trim()) {
        useAnalysisStore.getState().clearDiagnostics();
        return;
      }

      debounceRef.current = setTimeout(() => {
        sendCodeUpdate(newCode, language);
      }, 500);
    },
    [language, onCodeChange, sendCodeUpdate],
  );

  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
      hoverDisposableRef.current?.dispose();
      hoverDisposableRef.current = null;
      editorRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (connectionStatus !== 'connected' || !codeRef.current.trim()) return;
    sendCodeUpdate(codeRef.current, language);
  }, [connectionStatus, language, sendCodeUpdate]);

  useEffect(() => {
    const editor = editorRef.current;
    const model = editor?.getModel();
    if (!model) return;

    const markers = diagnostics.map((diagnostic) => ({
      startLineNumber: Math.max(1, diagnostic.line),
      startColumn: Math.max(1, diagnostic.column + 1),
      endLineNumber: Math.max(1, diagnostic.end_line ?? diagnostic.line),
      endColumn: Math.max(
        1,
        (diagnostic.end_column ?? diagnostic.column + 1) + 1,
      ),
      message: diagnostic.message,
      severity: toMarkerSeverity(diagnostic.severity),
      source: diagnostic.source,
      code: diagnostic.code ?? undefined,
    }));

    monaco.editor.setModelMarkers(model, 'realtime-analysis', markers);

    return () => {
      monaco.editor.setModelMarkers(model, 'realtime-analysis', []);
    };
  }, [diagnostics]);

  return (
    <div className="relative">
      <div className="absolute right-2 top-2 z-10 flex items-center space-x-2">
        <ConnectionStatusIndicator status={connectionStatus} />
        {lastAnalysisTime !== null && (
          <div className="rounded bg-gray-800 px-2 py-1 text-xs text-white">
            {Math.round(lastAnalysisTime)}ms
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

interface ConnectionStatusIndicatorProps {
  status: 'connecting' | 'connected' | 'disconnected' | 'error';
}

const ConnectionStatusIndicator: React.FC<ConnectionStatusIndicatorProps> = ({ status }) => {
  const display = {
    connecting: { color: 'bg-yellow-500', text: 'Connecting...', pulse: true },
    connected: { color: 'bg-green-500', text: 'Connected', pulse: false },
    disconnected: { color: 'bg-gray-500', text: 'Disconnected', pulse: false },
    error: { color: 'bg-red-500', text: 'Error', pulse: true },
  }[status];

  return (
    <div className="flex items-center space-x-1 rounded bg-gray-800 px-2 py-1 text-xs text-white">
      <div className={`h-2 w-2 rounded-full ${display.color} ${display.pulse ? 'animate-pulse' : ''}`} />
      <span>{display.text}</span>
    </div>
  );
};

export default CodeEditor;
