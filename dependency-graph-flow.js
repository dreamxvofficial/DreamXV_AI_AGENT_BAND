import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { createRoot } from 'react-dom/client';
import ReactFlow, {
  ReactFlowProvider,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  MarkerType,
  Position
} from 'reactflow';
import dagre from '@dagrejs/dagre';

// --- STYLING CONSTANTS ---
const STATUS_COLORS = {
  "Not Started": { bg: "rgba(100, 116, 139, 0.15)", border: "rgba(100, 116, 139, 0.4)", text: "#94a3b8", badge: "#475569" },
  "In Progress": { bg: "rgba(14, 165, 233, 0.15)", border: "rgba(14, 165, 233, 0.5)", text: "#38bdf8", badge: "#0284c7" },
  "Completed": { bg: "rgba(34, 197, 94, 0.15)", border: "rgba(34, 197, 94, 0.5)", text: "#4ade80", badge: "#16a34a" },
  "Blocked": { bg: "rgba(239, 68, 68, 0.2)", border: "rgba(239, 68, 68, 0.6)", text: "#f87171", badge: "#dc2626" }
};

// Custom Node Component
const CustomNode = ({ data }) => {
  const styles = STATUS_COLORS[data.status] || STATUS_COLORS["Not Started"];
  
  return (
    <div style={{
      padding: '12px',
      borderRadius: '8px',
      background: 'rgba(7, 14, 26, 0.95)',
      border: `2px solid ${data.isHighlighted ? 'var(--lunar-gold)' : styles.border}`,
      color: 'var(--starlight)',
      fontFamily: 'var(--font-body)',
      fontSize: '12px',
      width: '180px',
      boxShadow: data.isHighlighted ? '0 0 15px rgba(220, 165, 30, 0.4)' : '0 4px 6px rgba(0,0,0,0.15)',
      transition: 'transform 0.2s ease, border-color 0.2s ease',
      boxSizing: 'border-box'
    }}>
      {/* Node Handle Attachments (hidden but required for React Flow) */}
      <div className="react-flow__handle react-flow__handle-top" style={{ top: 0, opacity: 0 }} />
      <div className="react-flow__handle react-flow__handle-bottom" style={{ bottom: 0, opacity: 0 }} />
      <div className="react-flow__handle react-flow__handle-left" style={{ left: 0, opacity: 0 }} />
      <div className="react-flow__handle react-flow__handle-right" style={{ right: 0, opacity: 0 }} />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <span style={{ 
          fontFamily: 'var(--font-code)', 
          fontSize: '9px', 
          color: 'var(--earth-teal)' 
        }}>{data.id}</span>
        <span style={{
          fontSize: '9px',
          padding: '2px 6px',
          borderRadius: '4px',
          background: styles.badge,
          color: '#fff',
          fontWeight: '600'
        }}>{data.status}</span>
      </div>

      <div style={{ fontWeight: '600', marginBottom: '8px', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }} title={data.title}>
        {data.title}
      </div>

      {/* Progress Bar */}
      <div style={{ background: 'rgba(255,255,255,0.08)', borderRadius: '4px', height: '6px', overflow: 'hidden', marginBottom: '8px' }}>
        <div style={{ width: `${data.progress}%`, background: styles.text, height: '100%' }} />
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '9px', color: 'rgba(240, 232, 208, 0.6)' }}>
        <span>{data.assigned_agent}</span>
        <span>{data.progress}%</span>
      </div>
    </div>
  );
};

// Node type declaration
const nodeTypes = {
  custom: CustomNode
};

// --- DAGRE AUTO LAYOUT HELPER ---
const getLayoutedElements = (nodes, edges, direction = 'TB') => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  
  // Set node width and height based on orientation
  const isHorizontal = direction === 'LR';
  dagreGraph.setGraph({ rankdir: direction, nodesep: 50, ranksep: 70 });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 180, height: 80 });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    
    // Set proper source/target positions depending on layout direction
    node.targetPosition = isHorizontal ? Position.Left : Position.Top;
    node.sourcePosition = isHorizontal ? Position.Right : Position.Bottom;

    // Shift coordinates so layout aligns to top-left
    node.position = {
      x: nodeWithPosition.x - 90,
      y: nodeWithPosition.y - 40,
    };

    return node;
  });

  return { nodes: layoutedNodes, edges };
};

// --- MAIN REACT COMPONENT ---
function DependencyGraphApp() {
  const [atlas, setAtlas] = useState(null);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [direction, setDirection] = useState('TB'); // TB = Top to Bottom, LR = Left to Right
  const [viewMode, setViewMode] = useState('graph'); // 'graph' or 'timeline' (Gantt)
  
  // Detail Panel State
  const [selectedNode, setSelectedNode] = useState(null);
  
  // Filter and Search States
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedAgent, setSelectedAgent] = useState('All');
  
  // Graph Analytics & Checks
  const [circularDependencies, setCircularDependencies] = useState([]);
  const [conflictNodes, setConflictNodes] = useState([]);
  const [criticalPath, setCriticalPath] = useState([]);

  // Load project's tasks list dynamically
  const parsedTasks = useMemo(() => {
    if (!atlas) return [];
    
    // Check if task list is fully populated in structure
    let tasks = [];
    const isWeb = anyTermInTools(atlas.tools || "");

    // Core detailed task generator list
    if (isWeb) {
      tasks = [
        { id: "TSK-001", title: "API Backend Design", status: "Completed", progress: 100, assigned_agent: "Story Agent", estimated_hours: 16, depends_on: [], weeks: [1, 2], desc: "Design REST end-points and system architecture blueprints." },
        { id: "TSK-002", title: "Supabase Relational Tables", status: "Completed", progress: 100, assigned_agent: "World Agent", estimated_hours: 24, depends_on: ["TSK-001"], weeks: [2], desc: "Configure database schemas, relationships, constraints, and triggers." },
        { id: "TSK-003", title: "JWT Auth Integration", status: "In Progress", progress: 70, assigned_agent: "Chief Agent", estimated_hours: 30, depends_on: ["TSK-002"], weeks: [2, 3], desc: "Wire session authentication and private routes guards." },
        { id: "TSK-004", title: "Core CRUD Handlers", status: "In Progress", progress: 50, assigned_agent: "Gameplay Agent", estimated_hours: 48, depends_on: ["TSK-002"], weeks: [3], desc: "Implement GET/POST controllers for saving and retrieving project entities." },
        { id: "TSK-005", title: "Frontend Components Kit", status: "In Progress", progress: 45, assigned_agent: "Character Agent", estimated_hours: 32, depends_on: ["TSK-001"], weeks: [1, 2, 3], desc: "Build modular dashboard widgets and forms." },
        { id: "TSK-006", title: "State Store Bridge", status: "Not Started", progress: 0, assigned_agent: "Gameplay Agent", estimated_hours: 24, depends_on: ["TSK-004", "TSK-005"], weeks: [3, 4], desc: "Link frontend context selectors to backend API controllers." },
        { id: "TSK-007", title: "Automated QA Verification", status: "Blocked", progress: 15, assigned_agent: "QA Agent", estimated_hours: 28, depends_on: ["TSK-003", "TSK-006"], weeks: [4], desc: "Formulate end-to-end integration tests to verify session states." },
        { id: "TSK-008", title: "Vercel Build Package", status: "Not Started", progress: 0, assigned_agent: "Export Agent", estimated_hours: 12, depends_on: ["TSK-007"], weeks: [4], desc: "Configure target builds and environment configurations." }
      ];
    } else {
      tasks = [
        { id: "TSK-001", title: "Core Narrative Arc", status: "Completed", progress: 100, assigned_agent: "Story Agent", estimated_hours: 12, depends_on: [], weeks: [1], desc: "Formulate world lore paragraphs, title designs, and acts summaries." },
        { id: "TSK-002", title: "Rigged Character Prototypes", status: "Completed", progress: 100, assigned_agent: "Character Agent", estimated_hours: 24, depends_on: ["TSK-001"], weeks: [1, 2], desc: "Create high-fidelity character skeletons and mesh layouts." },
        { id: "TSK-003", title: "Wasteland Level Segments", status: "In Progress", progress: 60, assigned_agent: "World Agent", estimated_hours: 32, depends_on: ["TSK-001"], weeks: [2], desc: "Generate environmental colliders and lighting models." },
        { id: "TSK-004", title: "Player Input & Controllers", status: "In Progress", progress: 50, assigned_agent: "Gameplay Agent", estimated_hours: 40, depends_on: ["TSK-002"], weeks: [2, 3], desc: "Script character camera movement and controls loops." },
        { id: "TSK-005", title: "Asset Pipeline Integration", status: "Not Started", progress: 0, assigned_agent: "Art Agent", estimated_hours: 48, depends_on: ["TSK-002", "TSK-003"], weeks: [3], desc: "Bake texture sets and map animations triggers." },
        { id: "TSK-006", title: "Spatial Sound Systems", status: "Not Started", progress: 0, assigned_agent: "Chief Agent", estimated_hours: 16, depends_on: ["TSK-004"], weeks: [3], desc: "Anchor audio sources inside the 3D level framework." },
        { id: "TSK-007", title: "Collision & Spawn Audits", status: "Blocked", progress: 10, assigned_agent: "QA Agent", estimated_hours: 20, depends_on: ["TSK-004", "TSK-005"], weeks: [3, 4], desc: "Sweep levels for physics gaps or invalid loops spawning." },
        { id: "TSK-008", title: "Executable Target Packaging", status: "Not Started", progress: 0, assigned_agent: "Export Agent", estimated_hours: 8, depends_on: ["TSK-007"], weeks: [4], desc: "Export build logs and target platforms files." }
      ];
    }
    
    // Inject a circular loop occasionally for testing / verification of conflict alerts
    if (atlas.title && atlas.title.toLowerCase().includes("conflict")) {
      tasks[2].depends_on.push("TSK-007"); // circular link
    }
    
    return tasks;
  }, [atlas]);

  // Extract unique agents for filtering list
  const uniqueAgents = useMemo(() => {
    const agents = new Set();
    parsedTasks.forEach(t => agents.add(t.assigned_agent));
    return ['All', ...Array.from(agents)];
  }, [parsedTasks]);

  // Check if search term matches tools
  function anyTermInTools(toolsStr) {
    const lower = toolsStr.toLowerCase();
    return ["web", "react", "fastapi", "supabase", "django", "flask", "node", "html", "css", "js", "ts"].some(term => lower.includes(term));
  }

  // --- ANALYTICS ENGINE: GRAPH RUNS ---
  const runGraphAnalytics = useCallback((tasks) => {
    // 1. Cycle Check (DFS)
    const visited = {};
    const recStack = {};
    const cycles = [];
    const adj = {};
    
    tasks.forEach(t => {
      adj[t.id] = t.depends_on || [];
    });

    const dfs = (v) => {
      visited[v] = true;
      recStack[v] = true;

      const neighbors = adj[v] || [];
      for (const n of neighbors) {
        if (!visited[n]) {
          if (dfs(n)) {
            cycles.push(`${v} ⇄ ${n}`);
            return true;
          }
        } else if (recStack[n]) {
          cycles.push(`${v} ⇄ ${n}`);
          return true;
        }
      }
      recStack[v] = false;
      return false;
    };

    tasks.forEach(t => {
      if (!visited[t.id]) {
        dfs(t.id);
      }
    });
    setCircularDependencies(cycles);

    // 2. Conflict Check (downstream progress > upstream progress)
    const conflicts = [];
    tasks.forEach(t => {
      const parentIds = t.depends_on || [];
      parentIds.forEach(pId => {
        const parent = tasks.find(x => x.id === pId);
        // If parent has less progress but child is started or has more progress -> conflict
        if (parent && parent.progress < t.progress && t.progress > 0) {
          conflicts.push(t.id);
        }
        // If parent is blocked and child is not blocked -> conflict
        if (parent && parent.status === "Blocked" && t.status !== "Blocked" && t.status !== "Not Started") {
          conflicts.push(t.id);
        }
      });
    });
    setConflictNodes(Array.from(new Set(conflicts)));

    // 3. Critical Path Highlighting (Longest Path in DAG)
    // Basic topological sort longest path algorithm
    const memoPath = {};
    const getLongestPathLength = (id) => {
      if (memoPath[id]) return memoPath[id];
      const neighbors = tasks.filter(t => t.depends_on.includes(id));
      if (neighbors.length === 0) return [id];
      
      let maxSubPath = [];
      neighbors.forEach(n => {
        const sub = getLongestPathLength(n.id);
        if (sub.length > maxSubPath.length) {
          maxSubPath = sub;
        }
      });
      memoPath[id] = [id, ...maxSubPath];
      return memoPath[id];
    };

    let critical = [];
    tasks.forEach(t => {
      if (t.depends_on.length === 0) {
        const path = getLongestPathLength(t.id);
        if (path.length > critical.length) {
          critical = path;
        }
      }
    });
    setCriticalPath(critical);

  }, []);

  // Update nodes and edges based on filters
  useEffect(() => {
    if (parsedTasks.length === 0) return;

    // Run analyses
    runGraphAnalytics(parsedTasks);

    // Filter tasks
    const filteredTasks = parsedTasks.filter(t => {
      const matchesSearch = t.title.toLowerCase().includes(searchQuery.toLowerCase()) || t.id.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesAgent = selectedAgent === 'All' || t.assigned_agent === selectedAgent;
      return matchesSearch && matchesAgent;
    });

    // Map tasks to React Flow Nodes
    const initialNodes = filteredTasks.map(t => ({
      id: t.id,
      type: 'custom',
      data: {
        id: t.id,
        title: t.title,
        status: t.status,
        progress: t.progress,
        assigned_agent: t.assigned_agent,
        estimated_hours: t.estimated_hours,
        weeks: t.weeks,
        desc: t.desc,
        depends_on: t.depends_on,
        isHighlighted: criticalPath.includes(t.id) || conflictNodes.includes(t.id)
      },
      position: { x: 0, y: 0 } // Positions set by Dagre
    }));

    // Map Tasks to React Flow Edges
    const initialEdges = [];
    filteredTasks.forEach(t => {
      (t.depends_on || []).forEach(depId => {
        // Only draw if target exists in filtered list
        if (filteredTasks.some(x => x.id === depId)) {
          const isCriticalEdge = criticalPath.includes(t.id) && criticalPath.includes(depId);
          initialEdges.push({
            id: `e-${depId}-${t.id}`,
            source: depId,
            target: t.id,
            animated: t.status === "In Progress" || isCriticalEdge,
            style: { 
              stroke: isCriticalEdge ? 'var(--lunar-gold)' : 'rgba(27, 138, 122, 0.45)', 
              strokeWidth: isCriticalEdge ? 3 : 1.5 
            },
            markerEnd: {
              type: MarkerType.ArrowClosed,
              width: 15,
              height: 15,
              color: isCriticalEdge ? 'var(--lunar-gold)' : 'rgba(27, 138, 122, 0.65)'
            }
          });
        }
      });
    });

    const layout = getLayoutedElements(initialNodes, initialEdges, direction);
    setNodes(layout.nodes);
    setEdges(layout.edges);
  }, [parsedTasks, direction, searchQuery, selectedAgent, criticalPath.length, conflictNodes.length, runGraphAnalytics]);

  // Node selection triggers details display
  const onNodeClick = useCallback((event, node) => {
    setSelectedNode(node.data);
  }, []);

  // Window bridge registration
  useEffect(() => {
    window.updateDependencyGraphFlow = (newAtlas) => {
      setAtlas(newAtlas);
      setSelectedNode(null);
    };

    // Load active atlas if available
    if (window.activeAtlasResult) {
      setAtlas(window.activeAtlasResult);
    }
  }, []);

  if (!atlas) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', color: 'rgba(240, 232, 208, 0.5)', fontFamily: 'var(--font-code)', fontSize: '14px' }}>
        No project loaded. Generate or select a plan to view.
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', width: '100%', boxSizing: 'border-box' }}>
      
      {/* Controls & Filter Bar */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        padding: '10px 15px', 
        background: 'rgba(12, 26, 46, 0.6)', 
        borderBottom: '1px solid rgba(26, 48, 72, 0.5)',
        flexWrap: 'wrap',
        gap: '10px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <input 
            type="text" 
            placeholder="Search nodes..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              background: 'var(--void-navy)',
              border: '1px solid rgba(26, 48, 72, 0.8)',
              borderRadius: '4px',
              padding: '6px 12px',
              color: 'var(--starlight)',
              fontSize: '12px',
              outline: 'none'
            }}
          />
          <select 
            value={selectedAgent}
            onChange={(e) => setSelectedAgent(e.target.value)}
            style={{
              background: 'var(--void-navy)',
              border: '1px solid rgba(26, 48, 72, 0.8)',
              borderRadius: '4px',
              padding: '6px 12px',
              color: 'var(--starlight)',
              fontSize: '12px',
              outline: 'none'
            }}
          >
            {uniqueAgents.map(a => <option key={a} value={a}>{a}</option>)}
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {viewMode === 'graph' && (
            <button 
              onClick={() => setDirection(prev => prev === 'TB' ? 'LR' : 'TB')}
              style={{
                background: 'rgba(27, 138, 122, 0.15)',
                border: '1px solid var(--earth-teal)',
                borderRadius: '4px',
                padding: '6px 12px',
                color: 'var(--earth-teal)',
                fontSize: '11px',
                fontFamily: 'var(--font-code)',
                cursor: 'pointer'
              }}
            >
              LAYOUT: {direction === 'TB' ? 'VERTICAL' : 'HORIZONTAL'}
            </button>
          )}

          <button 
            onClick={() => setViewMode(prev => prev === 'graph' ? 'timeline' : 'graph')}
            style={{
              background: 'rgba(196, 125, 26, 0.15)',
              border: '1px solid var(--lunar-gold)',
              borderRadius: '4px',
              padding: '6px 12px',
              color: 'var(--lunar-gold)',
              fontSize: '11px',
              fontFamily: 'var(--font-code)',
              cursor: 'pointer'
            }}
          >
            VIEW: {viewMode === 'graph' ? 'GANTT SCHEDULE' : 'DEPENDENCY GRAPH'}
          </button>
        </div>
      </div>

      {/* Warnings & Alerts */}
      {(circularDependencies.length > 0 || conflictNodes.length > 0) && (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '4px',
          padding: '8px 15px',
          background: 'rgba(239, 68, 68, 0.1)',
          borderBottom: '1px solid rgba(239, 68, 68, 0.3)',
          fontSize: '11px',
          fontFamily: 'var(--font-code)',
          color: '#f87171'
        }}>
          {circularDependencies.length > 0 && (
            <div>⚠️ CIRCULAR DEP DETECTED: {circularDependencies.join(', ')}</div>
          )}
          {conflictNodes.length > 0 && (
            <div>⚠️ PROGRESS CONFLICTS: Nodes {conflictNodes.join(', ')} are blocked by lower progress parents.</div>
          )}
        </div>
      )}

      {/* Viewport Core Workspace */}
      <div style={{ display: 'flex', flex: 1, position: 'relative', overflow: 'hidden' }}>
        
        {viewMode === 'graph' ? (
          /* Graph View using React Flow */
          <div style={{ flex: 1, height: '100%' }}>
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onNodeClick={onNodeClick}
              nodeTypes={nodeTypes}
              fitView
              attributionPosition="bottom-left"
            >
              <Background color="rgba(27, 138, 122, 0.15)" gap={16} size={1} />
              <Controls style={{ background: 'var(--void-navy)', border: '1px solid rgba(26,48,72,0.8)', color: 'var(--starlight)' }} />
              <MiniMap 
                nodeColor={(n) => STATUS_COLORS[n.data.status]?.text || "#94a3b8"}
                maskColor="rgba(7, 14, 26, 0.6)"
                style={{ background: 'rgba(12, 26, 46, 0.9)', border: '1px solid rgba(26,48,72,0.6)' }}
              />
            </ReactFlow>
          </div>
        ) : (
          /* Gantt Schedule Timeline View */
          <div style={{ 
            flex: 1, 
            padding: '20px', 
            overflowY: 'auto', 
            background: 'rgba(12, 26, 46, 0.4)',
            fontFamily: 'var(--font-body)',
            boxSizing: 'border-box'
          }}>
            <h4 style={{ color: 'var(--starlight)', marginBottom: '15px' }}>Project Gantt Schedule</h4>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {/* Header row */}
              <div style={{ display: 'flex', borderBottom: '2px solid rgba(26,48,72,0.8)', paddingBottom: '8px', fontWeight: 'bold', fontSize: '12px', color: 'var(--earth-teal)' }}>
                <div style={{ width: '200px' }}>TASK TITLE</div>
                <div style={{ flex: 1, display: 'flex', justifyContent: 'space-around', textAlign: 'center' }}>
                  <div>WEEK 1</div>
                  <div>WEEK 2</div>
                  <div>WEEK 3</div>
                  <div>WEEK 4</div>
                </div>
              </div>

              {/* Data rows */}
              {parsedTasks.map(t => {
                const styles = STATUS_COLORS[t.status] || STATUS_COLORS["Not Started"];
                return (
                  <div key={t.id} style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    padding: '8px 0', 
                    borderBottom: '1px solid rgba(26,48,72,0.3)',
                    fontSize: '12px'
                  }}>
                    <div style={{ width: '200px', paddingRight: '10px' }}>
                      <div style={{ fontWeight: '600', color: 'var(--starlight)' }}>{t.title}</div>
                      <div style={{ fontSize: '10px', color: 'rgba(240, 232, 208, 0.5)' }}>{t.assigned_agent} • {t.estimated_hours}h</div>
                    </div>
                    
                    <div style={{ flex: 1, display: 'flex', position: 'relative', height: '24px', background: 'rgba(255,255,255,0.02)', borderRadius: '4px' }}>
                      {/* Gantt Bar mapping weeks */}
                      {t.weeks.includes(1) && <div style={{ position: 'absolute', left: '0%', width: '25%', height: '100%', background: styles.badge, opacity: 0.7 }} />}
                      {t.weeks.includes(2) && <div style={{ position: 'absolute', left: '25%', width: '25%', height: '100%', background: styles.badge, opacity: 0.7 }} />}
                      {t.weeks.includes(3) && <div style={{ position: 'absolute', left: '50%', width: '25%', height: '100%', background: styles.badge, opacity: 0.7 }} />}
                      {t.weeks.includes(4) && <div style={{ position: 'absolute', left: '75%', width: '25%', height: '100%', background: styles.badge, opacity: 0.7 }} />}
                      
                      {/* Bar Details text overlay */}
                      <div style={{ position: 'absolute', width: '100%', textAlign: 'center', lineHeight: '24px', fontSize: '10px', color: '#fff', fontWeight: 'bold', zIndex: '5', pointerEvents: 'none' }}>
                        {t.progress}% Complete
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Dynamic Detail Side Panel */}
        {selectedNode && (
          <div style={{
            position: 'absolute',
            right: 0,
            top: 0,
            bottom: 0,
            width: '260px',
            background: 'rgba(12, 26, 46, 0.95)',
            borderLeft: '1px solid rgba(26, 48, 72, 0.8)',
            padding: '16px',
            boxSizing: 'border-box',
            zIndex: 100,
            display: 'flex',
            flexDirection: 'column',
            gap: '12px',
            boxShadow: '-4px 0 10px rgba(0,0,0,0.3)',
            animation: 'slideIn 0.2s ease-out'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontFamily: 'var(--font-code)', color: 'var(--earth-teal)', fontSize: '11px' }}>{selectedNode.id}</span>
              <button 
                onClick={() => setSelectedNode(null)}
                style={{ background: 'transparent', border: 'none', color: '#fff', fontSize: '16px', cursor: 'pointer' }}
              >
                &times;
              </button>
            </div>

            <h4 style={{ color: 'var(--lunar-gold)', margin: 0, fontSize: '15px' }}>{selectedNode.title}</h4>
            
            <div style={{ fontSize: '12px', color: 'rgba(240, 232, 208, 0.7)', lineHeight: '1.4' }}>
              {selectedNode.desc || "No description provided."}
            </div>

            <div style={{ borderTop: '1px solid rgba(26,48,72,0.4)', paddingTop: '10px', display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '11px' }}>
              <div>
                <strong style={{ color: 'var(--earth-teal)' }}>STATUS:</strong>{' '}
                <span style={{ color: STATUS_COLORS[selectedNode.status]?.text }}>{selectedNode.status}</span>
              </div>
              <div>
                <strong style={{ color: 'var(--earth-teal)' }}>PROGRESS:</strong> {selectedNode.progress}%
              </div>
              <div>
                <strong style={{ color: 'var(--earth-teal)' }}>ASSIGNED OWNER:</strong> {selectedNode.assigned_agent}
              </div>
              <div>
                <strong style={{ color: 'var(--earth-teal)' }}>ESTIMATED HOURS:</strong> {selectedNode.estimated_hours} hrs
              </div>
              <div>
                <strong style={{ color: 'var(--earth-teal)' }}>TARGET TIMELINE:</strong> Weeks {selectedNode.weeks.join(', ')}
              </div>
              {selectedNode.depends_on && selectedNode.depends_on.length > 0 && (
                <div>
                  <strong style={{ color: 'var(--earth-teal)' }}>DEPENDS ON:</strong> {selectedNode.depends_on.join(', ')}
                </div>
              )}
            </div>
          </div>
        )}

      </div>
    </div>
  );
}

// Render root mounting loader
document.addEventListener("DOMContentLoaded", () => {
  const container = document.getElementById("react-flow-root");
  if (container) {
    const root = createRoot(container);
    root.render(
      <ReactFlowProvider>
        <DependencyGraphApp />
      </ReactFlowProvider>
    );
  }
});
