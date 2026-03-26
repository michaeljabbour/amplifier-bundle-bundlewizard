# Phase 2: Bundle Files + Swift Models

> **Execution:** Use the subagent-driven-development workflow to implement this plan.

**Goal:** Create the two new bundle files in the `amplifier-bundle-bundlewizard` repo and build the Swift-side models, merge engine, service cleanup, and tab removal needed to consume structured graph state from the AI.

**Architecture:** The bundle repo gets `bundles/desktop.yaml` (inherits base bundle + adds canvas context) and `context/desktop-visual-adapter.md` (instructions telling the AI to emit `bundlewizard-graph` JSON). The Swift app gets a `BundlewizardGraphState` model matching the JSON schema, a `mergeAIState()` method on `GraphDocument`, `graph_state` message handling in `AmplifierService`, graph tab removal from `ContentView`, and a DOT flyout panel for large DOT blocks.

**Tech Stack:** YAML/Markdown (bundle), Swift 5 (SwiftUI, @Observable, Codable), Swift Testing (`@Suite`, `@Test`, `#expect`)

**Repos:**
- `amplifier-bundle-bundlewizard` at `/Users/michaeljabbour/dev/amplifier-bundle-bundlewizard/`
- `amplifier-app-bundlewizard-macos` at `/Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos/`

---

## Conventions (same as Phase 1)

- Swift tests: `import Testing`, `@Suite("Name")`, `@Test("desc")`, `#expect(...)`
- Models: `Codable, Sendable` structs in `Sources/BundlewizardCore/Models/`
- Services: `@Observable @MainActor public final class` in `Sources/BundlewizardCore/Services/`
- Views: `Sources/bundlewizard/Views/`
- Build: `cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift build`
- Test: `cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift test`

---

### Task 1: Create `bundles/desktop.yaml` in Bundle Repo

**Files:**
- Create: `/Users/michaeljabbour/dev/amplifier-bundle-bundlewizard/bundles/desktop.yaml`

**Note:** This task is in the **bundle repo**, not the macOS app repo.

**Step 1: Create the directory and file**

```bash
mkdir -p /Users/michaeljabbour/dev/amplifier-bundle-bundlewizard/bundles
```

Create `/Users/michaeljabbour/dev/amplifier-bundle-bundlewizard/bundles/desktop.yaml`:

```yaml
---
bundle:
  name: bundlewizard-desktop
  version: 0.4.0
  description: Bundlewizard with desktop visual canvas overlay.
includes:
  - bundle: bundlewizard
---

@bundlewizard:context/desktop-visual-adapter.md
```

**Step 2: Verify the file exists and is valid YAML**

```bash
cd /Users/michaeljabbour/dev/amplifier-bundle-bundlewizard && cat bundles/desktop.yaml
```

Expected: The file content above, printed to stdout.

**Step 3: Commit**

```bash
cd /Users/michaeljabbour/dev/amplifier-bundle-bundlewizard && git add bundles/desktop.yaml && git commit -m "feat: add desktop bundle variant for canvas-aware sessions

Inherits all base bundle content and adds the desktop-visual-adapter context
via @mention. CLI loads bundle.md (no canvas), desktop loads bundles/desktop.yaml."
```

---

### Task 2: Create `context/desktop-visual-adapter.md` in Bundle Repo

**Files:**
- Create: `/Users/michaeljabbour/dev/amplifier-bundle-bundlewizard/context/desktop-visual-adapter.md`

**Note:** This task is in the **bundle repo**, not the macOS app repo.

**Step 1: Create the file**

Create `/Users/michaeljabbour/dev/amplifier-bundle-bundlewizard/context/desktop-visual-adapter.md`:

```markdown
# Desktop Visual Canvas Adapter

You are running inside Bundlewizard Desktop with a visual canvas panel. Your responses are displayed in a **narrow chat panel** (25% width) alongside a **rich interactive canvas** (75% width).

## Graph State Emission

After any response that **adds, removes, or modifies** agents, tools, modes, recipes, context files, or advances the pipeline phase, emit a `bundlewizard-graph` fenced JSON block containing the **complete current state** of the bundle architecture.

### When to Emit

- After proposing agents, tools, modes, recipes, context files, or behaviors
- After modifying the bundle structure (adding/removing/renaming components)
- After advancing to a new pipeline phase (explore -> spec -> plan -> execute -> verify -> finish)
- After the user requests changes to the architecture

### When NOT to Emit

- Pure Q&A during exploration (no structural changes)
- Clarifying questions
- Error messages or apologies
- Responses that only contain prose/discussion without architectural changes

### JSON Schema

The block MUST be fenced with triple backticks and the language tag `bundlewizard-graph`:

~~~
```bundlewizard-graph
{
  "version": "1",
  "meta": {
    "bundleName": "<name of the bundle being designed>",
    "bundleVersion": "<version>",
    "phase": "<current phase: explore|spec|plan|execute|verify|finish>",
    "changes": ["<human-readable description of what changed since last emission>"]
  },
  "clusters": [
    {
      "id": "<unique-cluster-id>",
      "label": "<Display Name>",
      "parent": "<parent-cluster-id or null for top-level>",
      "icon": "<SF Symbol name, optional>"
    }
  ],
  "nodes": [
    {
      "id": "<unique-node-id>",
      "type": "<agent|tool|context|mode|recipe|state|behavior|bundle>",
      "cluster": "<cluster-id this node belongs to, or null>",
      "title": "<display name>",
      "subtitle": "<type label, e.g. 'Agent · reasoning'>",
      "properties": [
        {"label": "<property description>", "color": "<default|green|yellow|red|blue|purple|orange>"}
      ],
      "tooltip": "<longer description shown on hover>"
    }
  ],
  "edges": [
    {
      "from": "<source-node-id>",
      "to": "<target-node-id>",
      "edgeType": "<inheritance|spawn|toolRegistration|pipelineFlow|adversarial|loopBack|modeTransition|contextLoad|recipeNesting|stateReadWrite>",
      "label": "<optional edge label>"
    }
  ]
}
```
~~~

### Node Types

| Type | What It Represents |
|------|-------------------|
| `agent` | An AI agent in the bundle |
| `tool` | A tool module |
| `context` | A context document |
| `mode` | A mode definition |
| `recipe` | A recipe file |
| `state` | A state variable or store |
| `behavior` | A behavior bundle |
| `bundle` | A sub-bundle or included bundle |

### Edge Types

| Edge Type | Meaning |
|-----------|---------|
| `inheritance` | Bundle includes/inherits from another |
| `spawn` | Agent spawns/delegates to another agent |
| `toolRegistration` | Behavior registers a tool |
| `pipelineFlow` | Sequential flow through the pipeline |
| `adversarial` | Critic/adversarial relationship |
| `loopBack` | Convergence loop back |
| `modeTransition` | Mode transition trigger |
| `contextLoad` | Context document loaded by a component |
| `recipeNesting` | Recipe includes sub-recipe |
| `stateReadWrite` | Component reads/writes shared state |

### Emission Rules

1. **Full state every time** — each emission is the complete current model, not a delta. The `meta.changes` array documents what changed since last emission for human readability.
2. **Stable IDs** — use consistent kebab-case IDs for nodes across emissions (e.g., `cicd-explorer`, not a random UUID). This lets the canvas diff and animate transitions.
3. **Clusters group semantically** — group by phase (Exploration Phase, Generation Loop), by role (Agent Fleet, Tool Modules), or by function. Clusters can nest via `parent`.

## Chat UX Constraints

The chat panel is narrow. Every token matters.

- **Concise responses** — bullet points over paragraphs, short sentences, no filler
- **No redundant visualization** — don't describe architecture in text if you just emitted a graph block. The canvas IS the explanation. Say "Updated the canvas." not a paragraph restating what the canvas shows.
- **Compact questions** — during the explore interview, one focused question per response with 2-4 short multiple-choice options
- **Small DOT blocks** — only emit inline DOT for simple relationship diagrams (< 30 lines). Complex architecture goes to the canvas, not DOT.
- **Visual progress** — phase progression is shown on the canvas. Chat just says "Moving to spec phase." and the canvas updates.
- **Brief code** — full file contents belong in the file system (via tools), not pasted into chat
```

**Step 2: Verify the file**

```bash
cd /Users/michaeljabbour/dev/amplifier-bundle-bundlewizard && wc -l context/desktop-visual-adapter.md
```

Expected: ~100+ lines.

**Step 3: Commit**

```bash
cd /Users/michaeljabbour/dev/amplifier-bundle-bundlewizard && git add context/desktop-visual-adapter.md && git commit -m "feat: add desktop visual adapter context for canvas-aware AI behavior

Defines the bundlewizard-graph JSON schema, emission rules, node/edge types,
and chat UX constraints for narrow-panel desktop operation."
```

---

### Task 3: Swift `BundlewizardGraphState` Model

**Files:**
- Create: `Sources/BundlewizardCore/Models/BundlewizardGraphState.swift`
- Test: `Tests/BundlewizardCoreTests/BundlewizardGraphStateTests.swift` (create)

**Step 1: Write the failing test**

Create `Tests/BundlewizardCoreTests/BundlewizardGraphStateTests.swift`:

```swift
import Testing
import Foundation
@testable import BundlewizardCore

@Suite("BundlewizardGraphState")
struct BundlewizardGraphStateTests {
    static let sampleJSON = """
    {
      "version": "1",
      "meta": {
        "bundleName": "cicd-wizard",
        "bundleVersion": "1.0.0",
        "phase": "explore",
        "changes": ["Added cicd-explorer agent"]
      },
      "clusters": [
        {
          "id": "exploration-phase",
          "label": "Exploration Phase",
          "parent": "agent-fleet",
          "icon": "magnifyingglass"
        }
      ],
      "nodes": [
        {
          "id": "cicd-explorer",
          "type": "agent",
          "cluster": "exploration-phase",
          "title": "cicd-explorer",
          "subtitle": "Agent · reasoning",
          "properties": [
            {"label": "Adaptive interview", "color": "default"},
            {"label": "role: [reasoning]", "color": "green"}
          ],
          "tooltip": "Adaptive interview agent"
        }
      ],
      "edges": [
        {
          "from": "cicd-explorer",
          "to": "cicd-architect",
          "edgeType": "pipelineFlow",
          "label": "explore→design"
        }
      ]
    }
    """.data(using: .utf8)!

    @Test("Decodes valid JSON")
    func decodesValid() throws {
        let state = try JSONDecoder().decode(BundlewizardGraphState.self, from: Self.sampleJSON)
        #expect(state.version == "1")
        #expect(state.meta.bundleName == "cicd-wizard")
        #expect(state.meta.phase == "explore")
        #expect(state.meta.changes == ["Added cicd-explorer agent"])
        #expect(state.clusters.count == 1)
        #expect(state.clusters[0].id == "exploration-phase")
        #expect(state.clusters[0].parent == "agent-fleet")
        #expect(state.nodes.count == 1)
        #expect(state.nodes[0].id == "cicd-explorer")
        #expect(state.nodes[0].type == .agent)
        #expect(state.nodes[0].properties.count == 2)
        #expect(state.nodes[0].properties[0].color == .default)
        #expect(state.nodes[0].properties[1].color == .green)
        #expect(state.edges.count == 1)
        #expect(state.edges[0].edgeType == .pipelineFlow)
    }

    @Test("Roundtrips through encode/decode")
    func roundtrip() throws {
        let original = try JSONDecoder().decode(BundlewizardGraphState.self, from: Self.sampleJSON)
        let encoded = try JSONEncoder().encode(original)
        let decoded = try JSONDecoder().decode(BundlewizardGraphState.self, from: encoded)
        #expect(decoded.nodes.count == original.nodes.count)
        #expect(decoded.edges.count == original.edges.count)
        #expect(decoded.meta.phase == original.meta.phase)
    }

    @Test("All node types decode")
    func allNodeTypes() throws {
        for typeName in ["agent", "tool", "context", "mode", "recipe", "state", "behavior", "bundle"] {
            let json = """
            {"version":"1","meta":{},"clusters":[],"nodes":[{"id":"n","type":"\(typeName)","title":"N","properties":[]}],"edges":[]}
            """.data(using: .utf8)!
            let state = try JSONDecoder().decode(BundlewizardGraphState.self, from: json)
            #expect(state.nodes[0].type.rawValue == typeName)
        }
    }

    @Test("All edge types decode")
    func allEdgeTypes() throws {
        let edgeTypes = [
            "inheritance", "spawn", "toolRegistration", "pipelineFlow",
            "adversarial", "loopBack", "modeTransition", "contextLoad",
            "recipeNesting", "stateReadWrite"
        ]
        for et in edgeTypes {
            let json = """
            {"version":"1","meta":{},"clusters":[],"nodes":[],"edges":[{"from":"a","to":"b","edgeType":"\(et)"}]}
            """.data(using: .utf8)!
            let state = try JSONDecoder().decode(BundlewizardGraphState.self, from: json)
            #expect(state.edges[0].edgeType.rawValue == et)
        }
    }

    @Test("Empty state decodes")
    func emptyState() throws {
        let json = """
        {"version":"1","meta":{},"clusters":[],"nodes":[],"edges":[]}
        """.data(using: .utf8)!
        let state = try JSONDecoder().decode(BundlewizardGraphState.self, from: json)
        #expect(state.nodes.isEmpty)
        #expect(state.edges.isEmpty)
        #expect(state.clusters.isEmpty)
    }
}
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift test --filter BundlewizardGraphStateTests 2>&1 | tail -20
```

Expected: FAIL — `BundlewizardGraphState` doesn't exist.

**Step 3: Create the model**

Create `Sources/BundlewizardCore/Models/BundlewizardGraphState.swift`:

```swift
import Foundation

/// The complete graph state emitted by the AI in `bundlewizard-graph` fenced blocks.
/// This is a full-state snapshot — every emission contains the entire current model.
public struct BundlewizardGraphState: Codable, Sendable {
    public var version: String
    public var meta: Meta
    public var clusters: [Cluster]
    public var nodes: [Node]
    public var edges: [Edge]

    public init(
        version: String = "1",
        meta: Meta = Meta(),
        clusters: [Cluster] = [],
        nodes: [Node] = [],
        edges: [Edge] = []
    ) {
        self.version = version
        self.meta = meta
        self.clusters = clusters
        self.nodes = nodes
        self.edges = edges
    }
}

// MARK: - Meta

extension BundlewizardGraphState {
    public struct Meta: Codable, Sendable {
        public var bundleName: String?
        public var bundleVersion: String?
        public var phase: String?
        public var changes: [String]?

        public init(
            bundleName: String? = nil,
            bundleVersion: String? = nil,
            phase: String? = nil,
            changes: [String]? = nil
        ) {
            self.bundleName = bundleName
            self.bundleVersion = bundleVersion
            self.phase = phase
            self.changes = changes
        }
    }
}

// MARK: - Cluster

extension BundlewizardGraphState {
    public struct Cluster: Codable, Sendable, Identifiable {
        public var id: String
        public var label: String
        public var parent: String?
        public var icon: String?

        public init(id: String, label: String, parent: String? = nil, icon: String? = nil) {
            self.id = id
            self.label = label
            self.parent = parent
            self.icon = icon
        }
    }
}

// MARK: - Node

extension BundlewizardGraphState {
    public enum NodeType: String, Codable, Sendable {
        case agent, tool, context, mode, recipe, state, behavior, bundle
    }

    public struct NodeProperty: Codable, Sendable {
        public var label: String
        public var color: PropertyColor

        public init(label: String, color: PropertyColor = .default) {
            self.label = label
            self.color = color
        }
    }

    public enum PropertyColor: String, Codable, Sendable {
        case `default`, green, yellow, red, blue, purple, orange
    }

    public struct Node: Codable, Sendable, Identifiable {
        public var id: String
        public var type: NodeType
        public var cluster: String?
        public var title: String
        public var subtitle: String?
        public var properties: [NodeProperty]
        public var tooltip: String?

        public init(
            id: String,
            type: NodeType,
            cluster: String? = nil,
            title: String,
            subtitle: String? = nil,
            properties: [NodeProperty] = [],
            tooltip: String? = nil
        ) {
            self.id = id
            self.type = type
            self.cluster = cluster
            self.title = title
            self.subtitle = subtitle
            self.properties = properties
            self.tooltip = tooltip
        }
    }
}

// MARK: - Edge

extension BundlewizardGraphState {
    public enum EdgeKind: String, Codable, Sendable {
        case inheritance
        case spawn
        case toolRegistration
        case pipelineFlow
        case adversarial
        case loopBack
        case modeTransition
        case contextLoad
        case recipeNesting
        case stateReadWrite
    }

    public struct Edge: Codable, Sendable {
        public var from: String
        public var to: String
        public var edgeType: EdgeKind
        public var label: String?

        public init(from: String, to: String, edgeType: EdgeKind, label: String? = nil) {
            self.from = from
            self.to = to
            self.edgeType = edgeType
            self.label = label
        }
    }
}
```

**Step 4: Run tests to verify they pass**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift test --filter BundlewizardGraphStateTests 2>&1 | tail -20
```

Expected: PASS

**Step 5: Commit**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && git add -A && git commit -m "feat: add BundlewizardGraphState model matching bundlewizard-graph JSON schema

Codable structs for nodes (8 types), edges (10 types), clusters, and meta.
Used by GraphDocument.mergeAIState() to process AI graph emissions."
```

---

### Task 4: GraphDocument Merge Engine

**Files:**
- Modify: `Sources/BundlewizardCore/Bridge/GraphDocument.swift` (add mergeAIState method)
- Test: `Tests/BundlewizardCoreTests/MergeAIStateTests.swift` (create)

**Step 1: Write the failing test**

Create `Tests/BundlewizardCoreTests/MergeAIStateTests.swift`:

```swift
import Testing
@testable import BundlewizardCore

@Suite("GraphDocument.mergeAIState")
struct MergeAIStateTests {
    @Test("Adds new nodes from AI emission")
    @MainActor func addsNewNodes() {
        let doc = GraphDocument()
        let state = BundlewizardGraphState(nodes: [
            .init(id: "agent-1", type: .agent, title: "Explorer"),
            .init(id: "agent-2", type: .agent, title: "Architect"),
        ])
        doc.mergeAIState(state)

        #expect(doc.graph.nodes["agent-1"] != nil)
        #expect(doc.graph.nodes["agent-2"] != nil)
        #expect(doc.graph.nodes["agent-1"]?.title == "Explorer")
    }

    @Test("Adds edges from AI emission")
    @MainActor func addsEdges() {
        let doc = GraphDocument()
        let state = BundlewizardGraphState(
            nodes: [
                .init(id: "a", type: .agent, title: "A"),
                .init(id: "b", type: .agent, title: "B"),
            ],
            edges: [
                .init(from: "a", to: "b", edgeType: .pipelineFlow, label: "flow"),
            ]
        )
        doc.mergeAIState(state)

        #expect(doc.graph.edges.count == 1)
        let edge = doc.graph.edges.values.first!
        #expect(edge.fromNode == "a")
        #expect(edge.toNode == "b")
    }

    @Test("Preserves user positions on re-merge")
    @MainActor func preservesPositions() {
        let doc = GraphDocument()

        // First merge
        let state1 = BundlewizardGraphState(nodes: [
            .init(id: "agent-1", type: .agent, title: "Explorer"),
        ])
        doc.mergeAIState(state1)

        // User moves the node
        doc.updateNodePosition("agent-1", x: 500, y: 300)

        // Second merge (AI re-emits same node with updated title)
        let state2 = BundlewizardGraphState(nodes: [
            .init(id: "agent-1", type: .agent, title: "Explorer v2"),
        ])
        doc.mergeAIState(state2)

        // Position preserved, title updated
        #expect(doc.graph.nodes["agent-1"]?.x == 500)
        #expect(doc.graph.nodes["agent-1"]?.y == 300)
        #expect(doc.graph.nodes["agent-1"]?.title == "Explorer v2")
    }

    @Test("Keeps user-added nodes not in AI emission")
    @MainActor func keepsUserNodes() {
        let doc = GraphDocument()

        // AI adds a node
        let state1 = BundlewizardGraphState(nodes: [
            .init(id: "ai-node", type: .agent, title: "AI Node"),
        ])
        doc.mergeAIState(state1)

        // User adds their own node manually
        let userNode = GraphNode(id: "user-node", type: "agent", x: 100, y: 100, title: "User Node")
        doc.addNode(userNode)
        doc.markNodeAsUserAdded("user-node")

        // AI emits again without the user node
        let state2 = BundlewizardGraphState(nodes: [
            .init(id: "ai-node", type: .agent, title: "AI Node Updated"),
        ])
        doc.mergeAIState(state2)

        // User node should still be there
        #expect(doc.graph.nodes["user-node"] != nil)
        #expect(doc.graph.nodes["ai-node"]?.title == "AI Node Updated")
    }

    @Test("Removes AI nodes no longer in emission")
    @MainActor func removesStaleAINodes() {
        let doc = GraphDocument()

        // AI emits two nodes
        let state1 = BundlewizardGraphState(nodes: [
            .init(id: "keep", type: .agent, title: "Keep"),
            .init(id: "remove", type: .agent, title: "Remove"),
        ])
        doc.mergeAIState(state1)
        #expect(doc.graph.nodes.count == 2)

        // AI emits only one
        let state2 = BundlewizardGraphState(nodes: [
            .init(id: "keep", type: .agent, title: "Keep"),
        ])
        doc.mergeAIState(state2)

        #expect(doc.graph.nodes["keep"] != nil)
        #expect(doc.graph.nodes["remove"] == nil)
    }

    @Test("Stores latest AI state for diffing")
    @MainActor func storesLatestState() {
        let doc = GraphDocument()
        let state = BundlewizardGraphState(
            meta: .init(phase: "spec"),
            nodes: [.init(id: "n1", type: .agent, title: "N1")]
        )
        doc.mergeAIState(state)
        #expect(doc.latestAIState?.meta.phase == "spec")
    }
}
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift test --filter MergeAIStateTests 2>&1 | tail -20
```

Expected: FAIL — `mergeAIState`, `markNodeAsUserAdded`, `latestAIState` don't exist.

**Step 3: Implement the merge engine**

In `Sources/BundlewizardCore/Bridge/GraphDocument.swift`, add these properties and methods:

1. Add properties after `selectedNodeId` (line 8):

```swift
    /// Set of node IDs that were added by the user (not from AI).
    public var userAddedNodeIds: Set<String> = []

    /// The most recent AI-emitted graph state, used for diffing.
    public var latestAIState: BundlewizardGraphState?
```

2. Add the merge method and helper after the `// MARK: - Selection` section (after line 59):

```swift
    // MARK: - User-added tracking

    public func markNodeAsUserAdded(_ nodeId: String) {
        userAddedNodeIds.insert(nodeId)
    }

    // MARK: - AI State Merge

    /// Merge a new AI-emitted graph state into the current document.
    /// - Preserves user-added nodes (not in AI emission)
    /// - Preserves user positions for existing nodes
    /// - Adds new AI nodes with auto-layout positions
    /// - Removes AI nodes no longer in the emission
    /// - Replaces all edges from the AI emission
    public func mergeAIState(_ state: BundlewizardGraphState) {
        let aiNodeIds = Set(state.nodes.map(\.id))

        // 1. Remove AI-originated nodes that are no longer in the emission
        let currentNodeIds = Set(graph.nodes.keys)
        for nodeId in currentNodeIds {
            if !aiNodeIds.contains(nodeId) && !userAddedNodeIds.contains(nodeId) {
                graph.removeNode(nodeId)
            }
        }

        // 2. Add or update nodes from the AI emission
        for (index, aiNode) in state.nodes.enumerated() {
            if let existing = graph.nodes[aiNode.id] {
                // Update properties but preserve position
                let x = existing.x
                let y = existing.y
                graph.nodes[aiNode.id] = makeGraphNode(from: aiNode, x: x, y: y)
            } else {
                // New node — auto-layout position
                let x = 300.0
                let y = 80.0 + Double(index) * 160.0
                graph.nodes[aiNode.id] = makeGraphNode(from: aiNode, x: x, y: y)
            }
            // If this was previously user-added, remove that marking since AI now owns it
            userAddedNodeIds.remove(aiNode.id)
        }

        // 3. Replace all edges (edges are fully AI-controlled)
        let userEdgeIds = graph.edges.keys.filter { edgeId in
            // Keep edges connected to user-added nodes
            guard let edge = graph.edges[edgeId] else { return false }
            return userAddedNodeIds.contains(edge.fromNode) || userAddedNodeIds.contains(edge.toNode)
        }
        let userEdges = userEdgeIds.compactMap { graph.edges[$0] }

        graph.edges.removeAll()

        // Add AI edges
        for aiEdge in state.edges {
            let edgeId = "\(aiEdge.from)->\(aiEdge.to)"
            graph.edges[edgeId] = GraphEdge(
                id: edgeId,
                fromNode: aiEdge.from,
                toNode: aiEdge.to,
                edgeType: .dataFlow // Canvas edge type; visual styling uses the AI edge metadata
            )
        }

        // Restore user edges
        for edge in userEdges {
            graph.edges[edge.id] = edge
        }

        // 4. Store the latest state
        latestAIState = state
    }

    /// Convert a BundlewizardGraphState.Node to a GraphNode for the canvas.
    private func makeGraphNode(
        from aiNode: BundlewizardGraphState.Node,
        x: Double,
        y: Double
    ) -> GraphNode {
        // Convert properties to the existing AnyCodable format
        var props: [String: AnyCodable] = [:]
        props["nodeType"] = AnyCodable(aiNode.type.rawValue)
        if let subtitle = aiNode.subtitle {
            props["subtitle"] = AnyCodable(subtitle)
        }
        if let tooltip = aiNode.tooltip {
            props["tooltip"] = AnyCodable(tooltip)
        }
        if let cluster = aiNode.cluster {
            props["cluster"] = AnyCodable(cluster)
        }
        // Store property rows as a JSON array string for the tile view
        let propLabels = aiNode.properties.map { "\($0.color.rawValue):\($0.label)" }
        props["propertyRows"] = AnyCodable(propLabels)

        return GraphNode(
            id: aiNode.id,
            type: aiNode.type.rawValue,
            x: x,
            y: y,
            title: aiNode.title,
            properties: props
        )
    }
```

**Step 4: Run tests to verify they pass**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift test --filter MergeAIStateTests 2>&1 | tail -20
```

Expected: PASS

**Step 5: Run the full test suite**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift test 2>&1 | tail -20
```

Expected: All tests pass.

**Step 6: Commit**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && git add -A && git commit -m "feat: add mergeAIState() to GraphDocument for smart AI/user state merging

Preserves user positions, keeps user-added nodes, removes stale AI nodes,
replaces edges from AI emission. Stores latestAIState for diffing."
```

---

### Task 5: AmplifierService — Add `graph_state` Message Handling

**Files:**
- Modify: `Sources/BundlewizardCore/Services/AmplifierService.swift` (handleBridgeMessage, add document property)
- Modify: `Sources/bundlewizard/BundlewizardApp.swift` (wire document to service)
- Test: `Tests/BundlewizardCoreTests/GraphStateHandlingTests.swift` (create)

**Step 1: Write the failing test**

Create `Tests/BundlewizardCoreTests/GraphStateHandlingTests.swift`:

```swift
import Testing
import Foundation
@testable import BundlewizardCore

@Suite("graph_state message handling")
struct GraphStateHandlingTests {
    @Test("AmplifierService has a graphDocument property")
    @MainActor func hasGraphDocument() {
        let bm = BridgeManager()
        let service = AmplifierService(bridgeManager: bm)
        #expect(service.graphDocument != nil)
    }

    @Test("latestDOT is still accessible")
    @MainActor func latestDOTAccessible() {
        let bm = BridgeManager()
        let service = AmplifierService(bridgeManager: bm)
        #expect(service.latestDOT == nil)
    }
}
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift test --filter GraphStateHandlingTests 2>&1 | tail -20
```

Expected: FAIL — `graphDocument` property doesn't exist on AmplifierService.

**Step 3: Add graphDocument and graph_state handling**

In `Sources/BundlewizardCore/Services/AmplifierService.swift`:

1. Add the `graphDocument` property after `latestDOT` (around line 169):

```swift
    public var graphDocument = GraphDocument()
```

2. Add a `graph_state` case in `handleBridgeMessage` (in the `switch type` block, before the `default:` case around line 399). Add this case:

```swift
        case "graph_state":
            guard let data = json["data"] as? [String: Any] else {
                Log.warn("graph_state missing data field")
                break
            }
            do {
                let jsonData = try JSONSerialization.data(withJSONObject: data)
                let state = try JSONDecoder().decode(BundlewizardGraphState.self, from: jsonData)
                graphDocument.mergeAIState(state)
                Log.response("Graph state merged: \(state.nodes.count) nodes, \(state.edges.count) edges")
            } catch {
                Log.warn("Failed to decode graph_state: \(error.localizedDescription)")
            }
```

**Step 4: Run tests to verify they pass**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift test --filter GraphStateHandlingTests 2>&1 | tail -20
```

Expected: PASS

**Step 5: Update BundlewizardApp and ContentView to use the service's graphDocument**

In `Sources/bundlewizard/Views/ContentView.swift`, replace the local `@State private var document = GraphDocument()` (line 12) with a computed reference. Change:

```swift
    @State private var document = GraphDocument()
```

To: (remove this line — we'll get the document from the service)

Then update the two places where `document` is used:
- Line 66: `CanvasView(document: document)` → `CanvasView(document: service.graphDocument)`
- Line 68: `GraphView(document: document)` → `GraphView(document: service.graphDocument)`

And remove any remaining references to the local `document` variable in the `.onChange` blocks (the `parsedWorkflowSteps` one was already deleted in Phase 1).

**Step 6: Run full test suite**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift test 2>&1 | tail -20
```

Expected: All tests pass.

**Step 7: Commit**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && git add -A && git commit -m "feat: handle graph_state WebSocket messages in AmplifierService

Decodes BundlewizardGraphState from graph_state messages and calls
graphDocument.mergeAIState(). ContentView now uses service.graphDocument
instead of a local @State document."
```

---

### Task 6: Kill Graph Tab

**Files:**
- Modify: `Sources/bundlewizard/Views/ContentView.swift` (remove tab bar, rightTab state, graph tab, onChange for latestDOT)
- Keep: `Sources/bundlewizard/Views/GraphView.swift` (kept for DOT flyout, but no longer a tab)

**Step 1: No test needed — this is a view-only change**

**Step 2: Remove graph tab from ContentView**

In `Sources/bundlewizard/Views/ContentView.swift`, make these changes:

1. Delete the `rightTab` state and enum (lines 8, 14):
   ```swift
   @State private var rightTab: RightTab = .canvas   // DELETE
   enum RightTab { case canvas, graph }               // DELETE
   ```

2. Replace the right panel section (the VStack with tab bar + content switch, lines 49-73) with just the canvas:
   ```swift
                    // Right panel — canvas only
                    CanvasView(document: service.graphDocument)
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
   ```

3. Delete the `.onChange(of: service.latestDOT)` block (lines 76-80):
   ```swift
            .onChange(of: service.latestDOT) { _, newDOT in
                if newDOT != nil {
                    withAnimation(.easeInOut(duration: 0.2)) { rightTab = .graph }
                }
            }
   ```

4. Delete the `tabButton` helper method (lines 143-157) since it's no longer used.

**Step 3: Build to verify**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift build 2>&1 | tail -10
```

Expected: Build succeeds.

**Step 4: Run tests**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift test 2>&1 | tail -20
```

Expected: All pass.

**Step 5: Commit**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && git add -A && git commit -m "refactor: remove graph tab — canvas is the only right panel view

Eliminates tab switching race conditions. DOT graphs will render inline
in chat bubbles (already working via viz-js in MarkdownBubble).
GraphView.swift kept for future DOT flyout panel."
```

---

### Task 7: DOT Flyout Panel

**Files:**
- Create: `Sources/bundlewizard/Views/DOTFlyoutView.swift`
- Modify: `Sources/bundlewizard/Views/ContentView.swift` (add flyout overlay)
- Modify: `Sources/bundlewizard/Views/ChatView.swift` (add "View Full Graph" button for large DOT blocks)

**Step 1: Create the flyout view**

Create `Sources/bundlewizard/Views/DOTFlyoutView.swift`:

```swift
import SwiftUI
import WebKit
import BundlewizardCore

/// Slide-over flyout for viewing large DOT graphs at full size.
/// Opens from the right edge. Dismiss by clicking outside or pressing Escape.
struct DOTFlyoutView: View {
    let dotSource: String
    @Binding var isPresented: Bool
    @State private var svgContent: String = ""
    @State private var isRendering = false

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Text("Graph View")
                    .font(.system(size: 13, weight: .bold))
                Spacer()
                Button { withAnimation(.easeOut(duration: 0.2)) { isPresented = false } } label: {
                    Image(systemName: "xmark")
                        .font(.system(size: 12))
                        .foregroundStyle(.secondary)
                }
                .buttonStyle(.plain)
                .keyboardShortcut(.escape, modifiers: [])
            }
            .padding(12)
            .background(.bar)

            Divider()

            // SVG content
            if isRendering {
                ProgressView("Rendering graph...")
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if svgContent.isEmpty {
                Text("Failed to render graph")
                    .foregroundStyle(.secondary)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                SVGRenderedView(svg: svgContent)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
        .frame(width: 600)
        .background(Color(nsColor: .windowBackgroundColor))
        .task {
            await renderDOT()
        }
    }

    private func renderDOT() async {
        isRendering = true
        // Reuse the same dot CLI approach from GraphView
        let home = ProcessInfo.processInfo.environment["HOME"] ?? ""
        let dotPaths = [
            "/opt/homebrew/bin/dot",
            "/usr/local/bin/dot",
            home + "/.nix-profile/bin/dot",
            "/usr/bin/dot",
        ]
        guard let dotPath = dotPaths.first(where: { FileManager.default.isExecutableFile(atPath: $0) }) else {
            isRendering = false
            return
        }

        do {
            let svg = try await withCheckedThrowingContinuation { (cont: CheckedContinuation<String, Error>) in
                Task.detached {
                    let proc = Process()
                    proc.executableURL = URL(fileURLWithPath: dotPath)
                    proc.arguments = ["-Tsvg"]
                    let stdin = Pipe()
                    let stdout = Pipe()
                    proc.standardInput = stdin
                    proc.standardOutput = stdout
                    proc.standardError = Pipe()
                    try proc.run()
                    if let data = dotSource.data(using: .utf8) {
                        stdin.fileHandleForWriting.write(data)
                    }
                    stdin.fileHandleForWriting.closeFile()
                    proc.waitUntilExit()
                    if proc.terminationStatus == 0 {
                        let svgData = stdout.fileHandleForReading.readDataToEndOfFile()
                        cont.resume(returning: String(data: svgData, encoding: .utf8) ?? "")
                    } else {
                        cont.resume(throwing: GraphRenderError.dotFailed("exit code \(proc.terminationStatus)"))
                    }
                }
            }
            svgContent = svg
        } catch {
            Log.error("DOT flyout render failed: \(error.localizedDescription)")
        }
        isRendering = false
    }
}
```

**Step 2: Add flyout state to ContentView**

In `Sources/bundlewizard/Views/ContentView.swift`, add a state variable for the flyout (after `showHistory`):

```swift
    @State private var showDOTFlyout = false
    @State private var flyoutDOTSource: String = ""
```

Add the flyout overlay inside the `ZStack`, after the history flyout overlay and before the closing `}` of the ZStack:

```swift
            // DOT flyout overlay (right edge)
            if showDOTFlyout {
                HStack(spacing: 0) {
                    // Dim overlay to dismiss
                    Color.black.opacity(0.3)
                        .onTapGesture { withAnimation(.easeOut(duration: 0.2)) { showDOTFlyout = false } }

                    DOTFlyoutView(dotSource: flyoutDOTSource, isPresented: $showDOTFlyout)
                        .transition(.move(edge: .trailing))
                }
                .zIndex(10)
            }
```

Add a method that ChatView can call to trigger the flyout. Add an `onOpenDOTFlyout` environment action or simply use a binding. The simplest approach: add a callback closure or use `NotificationCenter`. For simplicity, add a method to AmplifierService:

In `Sources/BundlewizardCore/Services/AmplifierService.swift`, add:

```swift
    public var pendingDOTFlyout: String?
```

Then in ContentView, observe it:

```swift
            .onChange(of: service.pendingDOTFlyout) { _, dotSource in
                if let dotSource, !dotSource.isEmpty {
                    flyoutDOTSource = dotSource
                    withAnimation(.easeInOut(duration: 0.2)) { showDOTFlyout = true }
                    service.pendingDOTFlyout = nil
                }
            }
```

**Step 3: Add "View Full Graph" button to ChatView for large DOT blocks**

In `Sources/bundlewizard/Views/ChatView.swift`, in the `assistantBubble` view (around line 364), add a check for large DOT blocks. Replace:

```swift
    private var assistantBubble: some View {
        VStack(alignment: .trailing, spacing: 2) {
            MarkdownBubble(markdown: message.text)
                .frame(maxWidth: .infinity, alignment: .leading)
            copyButton(for: message.text)
        }
    }
```

With:

```swift
    private var assistantBubble: some View {
        VStack(alignment: .trailing, spacing: 2) {
            MarkdownBubble(markdown: message.text)
                .frame(maxWidth: .infinity, alignment: .leading)

            // Show "View Full Graph" for large DOT blocks
            if let dotBlock = AmplifierService.extractDOT(from: message.text),
               dotBlock.components(separatedBy: "\n").count > 40 {
                Button {
                    service.pendingDOTFlyout = dotBlock
                } label: {
                    Label("View Full Graph", systemImage: "arrow.up.left.and.arrow.down.right")
                        .font(.system(size: 10))
                }
                .buttonStyle(.bordered)
                .controlSize(.small)
            }

            copyButton(for: message.text)
        }
    }
```

**Step 4: Build and test**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift build 2>&1 | tail -10
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift test 2>&1 | tail -20
```

Expected: Build succeeds, all tests pass.

**Step 5: Commit**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && git add -A && git commit -m "feat: add DOT flyout panel for large graphs (>40 lines)

Large DOT blocks in chat show a 'View Full Graph' button that opens
a slide-over flyout from the right edge with zoom/pan SVG rendering.
Dismiss by clicking outside or pressing Escape."
```

---

## Phase 2 Complete Checklist

After all 7 tasks, verify:

```bash
# Swift tests
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift test 2>&1 | tail -10

# Build
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift build 2>&1 | tail -5

# Bundle files exist
ls -la /Users/michaeljabbour/dev/amplifier-bundle-bundlewizard/bundles/desktop.yaml
ls -la /Users/michaeljabbour/dev/amplifier-bundle-bundlewizard/context/desktop-visual-adapter.md
```

**What changed:**
1. `bundles/desktop.yaml` created — desktop bundle variant inheriting base + canvas context
2. `context/desktop-visual-adapter.md` created — AI instructions for graph emission + chat UX
3. `BundlewizardGraphState` model created — Codable structs matching JSON schema
4. `GraphDocument.mergeAIState()` added — smart diff/merge preserving user edits
5. `AmplifierService` handles `graph_state` messages — decodes and merges into graphDocument
6. Graph tab killed — canvas is the only right panel view
7. DOT flyout panel added — large DOT blocks get a "View Full Graph" button

**Next:** Phase 3 builds the rich canvas components.
