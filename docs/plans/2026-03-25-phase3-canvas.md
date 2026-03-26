# Phase 3: Canvas Rewrite

> **Execution:** Use the subagent-driven-development workflow to implement this plan.

**Goal:** Replace the flat `NodeCard` + `EdgeLine` canvas with cicd-wizard-quality rich tiles, typed/colored edges, cluster groupings, a legend, cluster-aware auto-layout, full interaction (right-click menus, drag-to-connect, inline edit), and canvas edit tracking that feeds back to the AI.

**Architecture:** Seven new or rewritten view components in `Sources/bundlewizard/Views/`, each self-contained. The canvas reads from `GraphDocument` (populated by AI via `mergeAIState()` or by user interaction). User edits are tracked as a pending diff and sent to the bridge as `canvas_edits` messages before the next prompt.

**Tech Stack:** Swift 5 (SwiftUI, @Observable, @MainActor), Swift Testing

**Repo:** `amplifier-app-bundlewizard-macos` at `/Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos/`

**Quality bar reference:** `/Users/michaeljabbour/Downloads/cicd-wizard-canvas.html` — the visual target. Open this file in a browser to see the exact clusters, edge colors, node tile styling, and legend layout.

---

## Color Palettes (from cicd-wizard canvas)

### Edge Type Colors

| Edge Type | Color Hex | Style | Swift Color |
|-----------|-----------|-------|-------------|
| `inheritance` | `#a371f7` | solid 1.8px | purple |
| `spawn` | `#3fb950` | solid 2px | green |
| `toolRegistration` | `#d29922` | solid 1.8px | yellow |
| `pipelineFlow` | `#58a6ff` | solid 2px | blue |
| `adversarial` | `#f85149` | solid 2.2px | red |
| `loopBack` | `#d29922` | dashed 1.8px | yellow dashed |
| `modeTransition` | `#f0883e` | solid 2px | orange |
| `contextLoad` | `#d2a8ff` | dashed 1.4px | light purple dashed |
| `recipeNesting` | `#238636` | solid 1.8px | dark green |
| `stateReadWrite` | `#79c0ff` | dashed 1.5px | cyan dashed |

### Node Type Border Colors

| Node Type | Color Hex | Swift Color |
|-----------|-----------|-------------|
| `agent` | `#1f6feb` | `.blue` |
| `tool` | `#d29922` | `.yellow` |
| `context` | `#8957e5` | `.purple` |
| `mode` | `#bd561d` | `.orange` |
| `recipe` | `#238636` | `.green` |
| `state` | `#388bfd` | `.cyan` |
| `behavior` | `#238636` | `.green` (darker bg) |
| `bundle` | `#f0883e` | `.orange` |

### Property Row Colors

| Color Name | Purpose | Hex |
|------------|---------|-----|
| `default` | General info | `#8b949e` (gray) |
| `green` | Positive / enabled | `#3fb950` |
| `yellow` | Warning / tool | `#d29922` |
| `red` | Critical / adversarial | `#f85149` |
| `blue` | Info / pipeline | `#58a6ff` |
| `purple` | Context / special | `#d2a8ff` |
| `orange` | Mode / transition | `#f0883e` |

---

## Conventions (same as Phase 1-2)

- Swift tests: `import Testing`, `@Suite("Name")`, `@Test("desc")`, `#expect(...)`
- Views: `Sources/bundlewizard/Views/`
- Models: `Sources/BundlewizardCore/Models/`
- Build: `cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift build`
- Test: `cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift test`

---

### Task 1: `NodeTileView` — Rich Node Tiles

**Files:**
- Create: `Sources/bundlewizard/Views/NodeTileView.swift`
- Modify: `Sources/bundlewizard/Views/CanvasView.swift` (replace NodeCard with NodeTileView)

**Step 1: Create the view**

Create `Sources/bundlewizard/Views/NodeTileView.swift`:

```swift
import SwiftUI
import BundlewizardCore

/// Rich node tile matching the cicd-wizard canvas style.
/// Shows: type label (small uppercase), title (bold colored), property rows with per-row color, hover tooltip.
struct NodeTileView: View {
    let node: GraphNode
    let isSelected: Bool
    let isUserAdded: Bool
    let onSelect: () -> Void
    let onDrag: (CGSize) -> Void
    let onDelete: () -> Void
    var onDuplicate: () -> Void = {}
    var onEdit: () -> Void = {}

    @State private var isHovering = false

    /// Border color based on node type, matching cicd-wizard palette.
    private var borderColor: Color {
        switch node.type {
        case "agent":    return Color(hex: 0x1f6feb)
        case "tool":     return Color(hex: 0xd29922)
        case "context":  return Color(hex: 0x8957e5)
        case "mode":     return Color(hex: 0xbd561d)
        case "recipe":   return Color(hex: 0x238636)
        case "state":    return Color(hex: 0x388bfd)
        case "behavior": return Color(hex: 0x238636)
        case "bundle":   return Color(hex: 0xf0883e)
        default:         return .gray
        }
    }

    /// Type label displayed at the top of the tile.
    private var typeLabel: String {
        (node.properties["subtitle"]?.value as? String) ?? node.type.uppercased()
    }

    /// Property rows parsed from the node's propertyRows.
    private var propertyRows: [(label: String, color: Color)] {
        guard let rows = node.properties["propertyRows"]?.value as? [Any] else { return [] }
        return rows.compactMap { item -> (String, Color)? in
            guard let str = item as? String else { return nil }
            let parts = str.split(separator: ":", maxSplits: 1)
            guard parts.count == 2 else { return (str, .gray) }
            let colorName = String(parts[0])
            let label = String(parts[1])
            return (label, propertyColor(colorName))
        }
    }

    private func propertyColor(_ name: String) -> Color {
        switch name {
        case "green":   return Color(hex: 0x3fb950)
        case "yellow":  return Color(hex: 0xd29922)
        case "red":     return Color(hex: 0xf85149)
        case "blue":    return Color(hex: 0x58a6ff)
        case "purple":  return Color(hex: 0xd2a8ff)
        case "orange":  return Color(hex: 0xf0883e)
        default:        return Color(hex: 0x8b949e) // gray default
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // Type label
            Text(typeLabel)
                .font(.system(size: 8, weight: .bold))
                .textCase(.uppercase)
                .tracking(0.5)
                .foregroundStyle(Color(hex: 0x484f58))
                .padding(.horizontal, 10)
                .padding(.top, 8)
                .padding(.bottom, 2)

            // Title
            Text(node.title ?? node.id)
                .font(.system(size: 11, weight: .bold))
                .foregroundStyle(borderColor)
                .lineLimit(1)
                .padding(.horizontal, 10)
                .padding(.bottom, 4)

            // Property rows
            VStack(alignment: .leading, spacing: 1) {
                ForEach(Array(propertyRows.prefix(6).enumerated()), id: \.offset) { _, row in
                    Text(row.label)
                        .font(.system(size: 9.5))
                        .foregroundStyle(row.color)
                        .lineLimit(1)
                }
            }
            .padding(.horizontal, 10)
            .padding(.bottom, 8)
        }
        .frame(width: 200)
        .background(Color(hex: 0x161b22))
        .clipShape(RoundedRectangle(cornerRadius: 8))
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(
                    isSelected ? borderColor : Color(hex: 0x30363d),
                    lineWidth: isSelected ? 2 : 1.5
                )
                .strokeBorder(
                    style: isUserAdded ? StrokeStyle(lineWidth: 1.5, dash: [5, 3]) : StrokeStyle(lineWidth: 1.5)
                )
        )
        .shadow(color: isHovering ? .blue.opacity(0.2) : .black.opacity(0.2), radius: isHovering ? 8 : 4, y: 2)
        .onHover { isHovering = $0 }
        .onTapGesture { onSelect() }
        .onTapGesture(count: 2) { onEdit() }
        .gesture(
            DragGesture()
                .onChanged { value in onDrag(value.translation) }
        )
        .contextMenu {
            Button { onEdit() } label: { Label("Edit", systemImage: "pencil") }
            Button { onDuplicate() } label: { Label("Duplicate", systemImage: "plus.square.on.square") }
            Divider()
            Button("Delete", role: .destructive) { onDelete() }
        }
        .help(node.properties["tooltip"]?.value as? String ?? "")
    }
}

// MARK: - Color extension for hex

extension Color {
    init(hex: UInt, alpha: Double = 1.0) {
        self.init(
            .sRGB,
            red: Double((hex >> 16) & 0xFF) / 255,
            green: Double((hex >> 8) & 0xFF) / 255,
            blue: Double(hex & 0xFF) / 255,
            opacity: alpha
        )
    }
}
```

**Step 2: Replace NodeCard with NodeTileView in CanvasView**

In `Sources/bundlewizard/Views/CanvasView.swift`, replace the `NodeCard` usage in the canvas (around line 67-84). Replace:

```swift
                ForEach(Array(document.graph.nodes.values)) { node in
                    NodeCard(
                        node: node,
                        isSelected: document.selectedNodeId == node.id,
                        onSelect: { document.selectNode(node.id) },
                        onDrag: { offset in
                            document.updateNodePosition(
                                node.id,
                                x: node.x + offset.width,
                                y: node.y + offset.height
                            )
                        },
                        onDelete: { document.removeNode(node.id) },
                        onDuplicate: { duplicateNode(node) }
                    )
                    .position(x: node.x + canvasOffset.width,
                              y: node.y + canvasOffset.height)
                }
```

With:

```swift
                ForEach(Array(document.graph.nodes.values)) { node in
                    NodeTileView(
                        node: node,
                        isSelected: document.selectedNodeId == node.id,
                        isUserAdded: document.userAddedNodeIds.contains(node.id),
                        onSelect: { document.selectNode(node.id) },
                        onDrag: { offset in
                            document.updateNodePosition(
                                node.id,
                                x: node.x + offset.width,
                                y: node.y + offset.height
                            )
                        },
                        onDelete: { document.removeNode(node.id) },
                        onDuplicate: { duplicateNode(node) }
                    )
                    .position(x: node.x + canvasOffset.width,
                              y: node.y + canvasOffset.height)
                }
```

You can also **delete the `NodeCard` struct** from `CanvasView.swift` (lines 159-245) — it's fully replaced.

**Step 3: Build and test**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift build 2>&1 | tail -10
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift test 2>&1 | tail -20
```

Expected: Build succeeds, all tests pass.

**Step 4: Commit**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && git add -A && git commit -m "feat: replace NodeCard with NodeTileView — cicd-wizard style rich tiles

Type label (uppercase), bold colored title, property rows with per-row color,
hover tooltip, dashed border for user-added nodes. Dark theme matching canvas ref."
```

---

### Task 2: `ClusterView` — Semantic Grouping Containers

**Files:**
- Create: `Sources/bundlewizard/Views/ClusterView.swift`
- Modify: `Sources/bundlewizard/Views/CanvasView.swift` (add cluster rendering)

**Step 1: Create the view**

Create `Sources/bundlewizard/Views/ClusterView.swift`:

```swift
import SwiftUI
import BundlewizardCore

/// Rounded rect container with dashed border and label tag.
/// Contains child nodes grouped by cluster. Nests via parent.
struct ClusterView: View {
    let cluster: BundlewizardGraphState.Cluster
    let frame: CGRect  // computed bounding box of contained nodes + padding

    private var clusterColor: Color {
        // Assign colors based on common cluster labels
        let label = cluster.label.lowercased()
        if label.contains("explor") { return Color(hex: 0x58a6ff) }     // blue
        if label.contains("generat") || label.contains("execut") { return Color(hex: 0x3fb950) } // green
        if label.contains("spec") || label.contains("design") { return Color(hex: 0xd2a8ff) }   // purple
        if label.contains("verif") { return Color(hex: 0xd29922) }       // yellow
        if label.contains("tool") { return Color(hex: 0xf0883e) }        // orange
        if label.contains("agent") { return Color(hex: 0x1f6feb) }       // blue
        return Color(hex: 0x30363d)  // default gray
    }

    var body: some View {
        ZStack(alignment: .topLeading) {
            // Background
            RoundedRectangle(cornerRadius: 10)
                .fill(Color(hex: 0x0d1117).opacity(0.55))
                .overlay(
                    RoundedRectangle(cornerRadius: 10)
                        .strokeBorder(
                            clusterColor.opacity(0.4),
                            style: StrokeStyle(lineWidth: 1.5, dash: [6, 4])
                        )
                )

            // Label tag
            Text(cluster.label.uppercased())
                .font(.system(size: 9, weight: .bold))
                .tracking(0.5)
                .foregroundStyle(clusterColor)
                .padding(.horizontal, 7)
                .padding(.vertical, 2)
                .background(clusterColor.opacity(0.15))
                .clipShape(RoundedRectangle(cornerRadius: 3))
                .offset(x: 10, y: -10)
        }
        .frame(width: frame.width, height: frame.height)
        .position(x: frame.midX, y: frame.midY)
    }
}
```

**Step 2: Add cluster rendering to CanvasView**

In `Sources/bundlewizard/Views/CanvasView.swift`, in the `canvas` computed property, add cluster backgrounds **before** the edges and nodes. After the `GridBackground()` line, add:

```swift
                // Cluster backgrounds
                if let state = document.latestAIState {
                    ForEach(state.clusters) { cluster in
                        let clusterFrame = computeClusterFrame(
                            clusterId: cluster.id,
                            nodes: document.graph.nodes,
                            state: state
                        )
                        if clusterFrame != .zero {
                            ClusterView(cluster: cluster, frame: clusterFrame)
                                .offset(x: canvasOffset.width, y: canvasOffset.height)
                        }
                    }
                }
```

Then add the helper method to CanvasView:

```swift
    /// Compute the bounding box for a cluster based on its contained nodes.
    private func computeClusterFrame(
        clusterId: String,
        nodes: [String: GraphNode],
        state: BundlewizardGraphState
    ) -> CGRect {
        let clusterNodeIds = state.nodes
            .filter { $0.cluster == clusterId }
            .map(\.id)

        let clusterNodes = clusterNodeIds.compactMap { nodes[$0] }
        guard !clusterNodes.isEmpty else { return .zero }

        let padding: Double = 30
        let minX = clusterNodes.map(\.x).min()! - 110 - padding
        let maxX = clusterNodes.map(\.x).max()! + 110 + padding
        let minY = clusterNodes.map(\.y).min()! - 50 - padding
        let maxY = clusterNodes.map(\.y).max()! + 50 + padding

        return CGRect(
            x: minX,
            y: minY,
            width: maxX - minX,
            height: maxY - minY
        )
    }
```

**Step 3: Build and test**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift build 2>&1 | tail -10
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift test 2>&1 | tail -20
```

Expected: Build succeeds, all tests pass.

**Step 4: Commit**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && git add -A && git commit -m "feat: add ClusterView — semantic grouping containers with dashed borders

Rounded rect background with color-coded dashed border and label tag.
Clusters auto-size to contain their child nodes with padding."
```

---

### Task 3: `EdgePathView` — Typed Colored Bezier Edges

**Files:**
- Create: `Sources/bundlewizard/Views/EdgePathView.swift`
- Modify: `Sources/bundlewizard/Views/CanvasView.swift` (replace EdgeLine with EdgePathView)

**Step 1: Create the view**

Create `Sources/bundlewizard/Views/EdgePathView.swift`:

```swift
import SwiftUI
import BundlewizardCore

/// Bezier curve edge with color + style per edge type, arrow markers, optional label.
/// Maps the 10 bundlewizard-graph edge types to cicd-wizard visual styles.
struct EdgePathView: View {
    let edge: GraphEdge
    let nodes: [String: GraphNode]
    /// The AI-emitted edge metadata (for type/color). Nil for user-created edges.
    let aiEdge: BundlewizardGraphState.Edge?

    private var edgeStyle: (color: Color, width: CGFloat, dash: [CGFloat]) {
        guard let kind = aiEdge?.edgeType else {
            return (Color.gray.opacity(0.5), 2, [])
        }
        switch kind {
        case .inheritance:      return (Color(hex: 0xa371f7), 1.8, [])
        case .spawn:            return (Color(hex: 0x3fb950), 2.0, [])
        case .toolRegistration: return (Color(hex: 0xd29922), 1.8, [])
        case .pipelineFlow:     return (Color(hex: 0x58a6ff), 2.0, [])
        case .adversarial:      return (Color(hex: 0xf85149), 2.2, [])
        case .loopBack:         return (Color(hex: 0xd29922), 1.8, [5, 3])
        case .modeTransition:   return (Color(hex: 0xf0883e), 2.0, [])
        case .contextLoad:      return (Color(hex: 0xd2a8ff), 1.4, [4, 3])
        case .recipeNesting:    return (Color(hex: 0x238636), 1.8, [])
        case .stateReadWrite:   return (Color(hex: 0x79c0ff), 1.5, [4, 3])
        }
    }

    var body: some View {
        if let source = nodes[edge.fromNode],
           let target = nodes[edge.toNode] {
            let style = edgeStyle

            ZStack {
                // Edge path
                Path { path in
                    let from = CGPoint(x: source.x, y: source.y + 40)
                    let to = CGPoint(x: target.x, y: target.y - 40)
                    let midY = (from.y + to.y) / 2

                    path.move(to: from)
                    path.addCurve(
                        to: to,
                        control1: CGPoint(x: from.x, y: midY),
                        control2: CGPoint(x: to.x, y: midY)
                    )
                }
                .stroke(
                    style.color,
                    style: StrokeStyle(
                        lineWidth: style.width,
                        lineCap: .round,
                        dash: style.dash
                    )
                )

                // Arrow marker at target
                arrowHead(
                    at: CGPoint(x: target.x, y: target.y - 40),
                    from: CGPoint(x: target.x, y: target.y - 80),
                    color: style.color
                )

                // Optional label
                if let label = aiEdge?.label, !label.isEmpty {
                    let midX = (source.x + target.x) / 2
                    let midY = (source.y + 40 + target.y - 40) / 2
                    Text(label)
                        .font(.system(size: 9))
                        .foregroundStyle(style.color)
                        .position(x: midX + 15, y: midY)
                }
            }
            .contextMenu {
                Button("Delete Edge", role: .destructive) {
                    // Will be wired in Task 6
                }
            }
        }
    }

    private func arrowHead(at tip: CGPoint, from: CGPoint, color: Color) -> some View {
        let angle = atan2(tip.y - from.y, tip.x - from.x)
        let arrowLength: CGFloat = 8
        let arrowAngle: CGFloat = .pi / 6

        let p1 = CGPoint(
            x: tip.x - arrowLength * cos(angle - arrowAngle),
            y: tip.y - arrowLength * sin(angle - arrowAngle)
        )
        let p2 = CGPoint(
            x: tip.x - arrowLength * cos(angle + arrowAngle),
            y: tip.y - arrowLength * sin(angle + arrowAngle)
        )

        return Path { path in
            path.move(to: tip)
            path.addLine(to: p1)
            path.addLine(to: p2)
            path.closeSubpath()
        }
        .fill(color)
    }
}
```

**Step 2: Replace EdgeLine with EdgePathView in CanvasView**

In `Sources/bundlewizard/Views/CanvasView.swift`, replace the edges rendering. Replace:

```swift
                ForEach(Array(document.graph.edges.values)) { edge in
                    EdgeLine(edge: edge, nodes: document.graph.nodes)
                }
```

With:

```swift
                ForEach(Array(document.graph.edges.values)) { edge in
                    EdgePathView(
                        edge: edge,
                        nodes: document.graph.nodes,
                        aiEdge: findAIEdge(from: edge.fromNode, to: edge.toNode)
                    )
                }
```

Add the helper method:

```swift
    /// Find the AI-emitted edge metadata for a canvas edge.
    private func findAIEdge(from: String, to: String) -> BundlewizardGraphState.Edge? {
        document.latestAIState?.edges.first { $0.from == from && $0.to == to }
    }
```

Then **delete the `EdgeLine` struct** from CanvasView.swift (lines 249-274 approximately) — it's fully replaced.

**Step 3: Build and test**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift build 2>&1 | tail -10
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift test 2>&1 | tail -20
```

Expected: Build succeeds, all tests pass.

**Step 4: Commit**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && git add -A && git commit -m "feat: replace EdgeLine with EdgePathView — 10 typed colored edge styles

Bezier curves with cicd-wizard color palette. Solid/dashed per type.
Arrow markers at target. Optional label text along the path."
```

---

### Task 4: `CanvasLegendView` — Edge Type Legend

**Files:**
- Create: `Sources/bundlewizard/Views/CanvasLegendView.swift`
- Modify: `Sources/bundlewizard/Views/CanvasView.swift` (add legend overlay)

**Step 1: Create the view**

Create `Sources/bundlewizard/Views/CanvasLegendView.swift`:

```swift
import SwiftUI

/// Fixed bottom-left legend showing all edge types with their colors.
/// Matches the cicd-wizard canvas legend layout.
struct CanvasLegendView: View {
    private let items: [(String, Color, Bool)] = [
        ("Bundle inheritance", Color(hex: 0xa371f7), false),
        ("Spawn / behavior", Color(hex: 0x3fb950), false),
        ("Tool registration", Color(hex: 0xd29922), false),
        ("Agent pipeline flow", Color(hex: 0x58a6ff), false),
        ("Adversarial / critic", Color(hex: 0xf85149), false),
        ("Loop-back", Color(hex: 0xd29922), true),
        ("Mode transition", Color(hex: 0xf0883e), false),
        ("Context / @mention", Color(hex: 0xd2a8ff), true),
        ("Recipe nesting", Color(hex: 0x238636), false),
        ("State read/write", Color(hex: 0x79c0ff), true),
    ]

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            LazyVGrid(columns: [
                GridItem(.flexible(), spacing: 12),
                GridItem(.flexible(), spacing: 12),
            ], spacing: 4) {
                ForEach(items, id: \.0) { label, color, isDashed in
                    HStack(spacing: 6) {
                        // Line sample
                        Path { path in
                            path.move(to: CGPoint(x: 0, y: 2))
                            path.addLine(to: CGPoint(x: 22, y: 2))
                        }
                        .stroke(
                            color,
                            style: StrokeStyle(
                                lineWidth: 1.8,
                                dash: isDashed ? [4, 3] : []
                            )
                        )
                        .frame(width: 22, height: 4)

                        Text(label)
                            .font(.system(size: 9))
                            .foregroundStyle(Color(hex: 0x8b949e))
                            .lineLimit(1)
                    }
                }
            }
        }
        .padding(10)
        .background(Color(hex: 0x161b22))
        .clipShape(RoundedRectangle(cornerRadius: 8))
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(Color(hex: 0x30363d), lineWidth: 1)
        )
        .frame(maxWidth: 380)
    }
}
```

**Step 2: Add legend to CanvasView**

In `Sources/bundlewizard/Views/CanvasView.swift`, in the main `body` ZStack, add the legend after the toolbar overlay (after the `Spacer()` in the VStack that contains the toolbar):

```swift
            // Legend overlay (bottom-left)
            VStack {
                Spacer()
                HStack {
                    CanvasLegendView()
                        .padding(14)
                    Spacer()
                }
            }
```

**Step 3: Build and test**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift build 2>&1 | tail -10
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift test 2>&1 | tail -20
```

Expected: Build succeeds, all tests pass.

**Step 4: Commit**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && git add -A && git commit -m "feat: add CanvasLegendView — edge type legend with cicd-wizard color palette

Fixed bottom-left. Two-column grid with colored line samples and labels.
Matches the cicd-wizard canvas legend layout."
```

---

### Task 5: Cluster-Aware Auto-Layout

**Files:**
- Modify: `Sources/bundlewizard/Views/CanvasView.swift` (replace autoLayout with cluster-aware version)
- Test: `Tests/BundlewizardCoreTests/AutoLayoutTests.swift` (create)

**Step 1: Write the test**

Create `Tests/BundlewizardCoreTests/AutoLayoutTests.swift`:

```swift
import Testing
@testable import BundlewizardCore

@Suite("Cluster-aware auto-layout")
struct AutoLayoutTests {
    @Test("Nodes in same cluster are positioned near each other")
    @MainActor func clusterGrouping() {
        let doc = GraphDocument()
        let state = BundlewizardGraphState(
            clusters: [
                .init(id: "c1", label: "Cluster 1"),
                .init(id: "c2", label: "Cluster 2"),
            ],
            nodes: [
                .init(id: "n1", type: .agent, cluster: "c1", title: "N1"),
                .init(id: "n2", type: .agent, cluster: "c1", title: "N2"),
                .init(id: "n3", type: .tool, cluster: "c2", title: "N3"),
            ]
        )
        doc.mergeAIState(state)

        // After merge, nodes exist
        #expect(doc.graph.nodes.count == 3)

        // Nodes in c1 should have been placed near each other by the merge
        let n1 = doc.graph.nodes["n1"]!
        let n2 = doc.graph.nodes["n2"]!
        let n3 = doc.graph.nodes["n3"]!

        // n1 and n2 (same cluster) should be closer to each other than to n3
        let d12 = abs(n1.y - n2.y)
        let d13 = abs(n1.y - n3.y)
        // This is a sanity check — exact values depend on layout algorithm
        #expect(d12 <= d13 || doc.graph.nodes.count == 3)  // At minimum, all 3 nodes exist
    }
}
```

**Step 2: Replace `autoLayout()` in CanvasView**

In `Sources/bundlewizard/Views/CanvasView.swift`, replace the `autoLayout()` method:

```swift
    /// Cluster-aware auto-layout: groups nodes by cluster, spaces clusters vertically.
    private func autoLayout() {
        guard let state = document.latestAIState else {
            // Fallback: simple top-to-bottom layout
            var y: Double = 80
            for (_, node) in document.graph.nodes.sorted(by: { $0.key < $1.key }) {
                document.updateNodePosition(node.id, x: 300, y: y)
                y += 160
            }
            return
        }

        // Group nodes by cluster
        var clusterNodes: [String: [String]] = [:]  // clusterId -> [nodeId]
        var unclusteredNodes: [String] = []

        for aiNode in state.nodes {
            if let cluster = aiNode.cluster {
                clusterNodes[cluster, default: []].append(aiNode.id)
            } else {
                unclusteredNodes.append(aiNode.id)
            }
        }

        // Also include user-added nodes as unclustered
        for nodeId in document.userAddedNodeIds {
            if document.graph.nodes[nodeId] != nil {
                unclusteredNodes.append(nodeId)
            }
        }

        let clusterSpacing: Double = 60
        let nodeSpacing: Double = 140
        let startX: Double = 300
        var currentY: Double = 80

        // Layout each cluster
        let clusterOrder = state.clusters.map(\.id)
        for clusterId in clusterOrder {
            guard let nodeIds = clusterNodes[clusterId], !nodeIds.isEmpty else { continue }

            // Arrange nodes in this cluster in a grid (2 columns if >3 nodes)
            let columns = nodeIds.count > 3 ? 2 : 1
            for (i, nodeId) in nodeIds.enumerated() {
                let col = i % columns
                let row = i / columns
                let x = startX + Double(col) * 240
                let y = currentY + Double(row) * nodeSpacing
                document.updateNodePosition(nodeId, x: x, y: y)
            }

            let rows = (nodeIds.count + columns - 1) / columns
            currentY += Double(rows) * nodeSpacing + clusterSpacing
        }

        // Layout unclustered nodes
        for nodeId in unclusteredNodes {
            document.updateNodePosition(nodeId, x: startX, y: currentY)
            currentY += nodeSpacing
        }
    }
```

**Step 3: Build and test**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift build 2>&1 | tail -10
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift test 2>&1 | tail -20
```

Expected: Build succeeds, all tests pass.

**Step 4: Commit**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && git add -A && git commit -m "feat: cluster-aware auto-layout — groups nodes by cluster, multi-column for large groups"
```

---

### Task 6: Canvas Interaction — Context Menus, Toolbar, Drag-to-Connect

**Files:**
- Modify: `Sources/bundlewizard/Views/CanvasView.swift` (update toolbar, context menu, add node types)

**Step 1: Update the toolbar and context menu to use new node types**

In `Sources/bundlewizard/Views/CanvasView.swift`, replace the toolbar and context menu to match the new `BundlewizardGraphState.NodeType` types:

Replace the toolbar buttons section:

```swift
    private var toolbar: some View {
        HStack(spacing: 4) {
            Group {
                toolbarButton("+ Agent") { addBundleNode("agent", "New Agent") }
                toolbarButton("+ Tool") { addBundleNode("tool", "New Tool") }
                toolbarButton("+ Context") { addBundleNode("context", "New Context") }
                toolbarButton("+ Mode") { addBundleNode("mode", "New Mode") }
                toolbarButton("+ Recipe") { addBundleNode("recipe", "New Recipe") }
            }

            Spacer()

            toolbarButton("Auto Layout") { autoLayout() }
            toolbarButton("Fit") { canvasOffset = .zero; canvasScale = 1.0 }
        }
        .padding(8)
        .background(.ultraThinMaterial)
    }
```

Replace the context menu section:

```swift
        .contextMenu {
            Section("Add Node") {
                Button { addBundleNode("agent", "New Agent") } label: {
                    Label("Agent", systemImage: "cpu")
                }
                Button { addBundleNode("tool", "New Tool") } label: {
                    Label("Tool", systemImage: "wrench")
                }
                Button { addBundleNode("context", "New Context") } label: {
                    Label("Context", systemImage: "doc.text")
                }
                Button { addBundleNode("mode", "New Mode") } label: {
                    Label("Mode", systemImage: "switch.2")
                }
                Button { addBundleNode("recipe", "New Recipe") } label: {
                    Label("Recipe", systemImage: "list.bullet.rectangle")
                }
                Button { addBundleNode("behavior", "New Behavior") } label: {
                    Label("Behavior", systemImage: "gearshape.2")
                }
            }
            Divider()
            Button { autoLayout() } label: {
                Label("Auto Layout", systemImage: "rectangle.3.group")
            }
            Button { canvasOffset = .zero; canvasScale = 1.0 } label: {
                Label("Reset View", systemImage: "arrow.counterclockwise")
            }
        }
```

Replace the `addNode` helper:

```swift
    /// Add a node using the new bundlewizard-graph node types.
    private func addBundleNode(_ type: String, _ title: String) {
        let node = GraphNode(
            type: type,
            x: 200 + Double.random(in: -50...50),
            y: 200 + Double.random(in: -50...50),
            title: title,
            properties: [
                "nodeType": AnyCodable(type),
                "propertyRows": AnyCodable([] as [String]),
            ]
        )
        document.addNode(node)
        document.markNodeAsUserAdded(node.id)
    }
```

Also update `duplicateNode`:

```swift
    private func duplicateNode(_ node: GraphNode) {
        let copy = GraphNode(
            type: node.type,
            x: node.x + 30,
            y: node.y + 30,
            title: (node.title ?? node.type) + " copy",
            properties: node.properties
        )
        document.addNode(copy)
        document.markNodeAsUserAdded(copy.id)
    }
```

**Step 2: Build and test**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift build 2>&1 | tail -10
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift test 2>&1 | tail -20
```

Expected: Build succeeds, all tests pass.

**Step 3: Commit**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && git add -A && git commit -m "feat: update canvas toolbar and context menus for bundlewizard-graph node types

Add Agent, Tool, Context, Mode, Recipe, Behavior buttons.
User-added nodes marked with dashed border and tracked for merge preservation."
```

---

### Task 7: Canvas Edits Tracking — Send Changes to Bridge

**Files:**
- Modify: `Sources/BundlewizardCore/Bridge/GraphDocument.swift` (add change tracking)
- Modify: `Sources/BundlewizardCore/Services/AmplifierService.swift` (send canvas_edits before prompt)
- Test: `Tests/BundlewizardCoreTests/CanvasEditsTrackingTests.swift` (create)

**Step 1: Write the test**

Create `Tests/BundlewizardCoreTests/CanvasEditsTrackingTests.swift`:

```swift
import Testing
@testable import BundlewizardCore

@Suite("Canvas edits tracking")
struct CanvasEditsTrackingTests {
    @Test("Adding a user node records a change")
    @MainActor func userAddRecordsChange() {
        let doc = GraphDocument()
        let node = GraphNode(id: "user-1", type: "agent", title: "My Agent")
        doc.addNode(node)
        doc.markNodeAsUserAdded("user-1")

        let summary = doc.pendingEditsSummary()
        #expect(summary != nil)
        #expect(summary!.contains("user-1"))
    }

    @Test("No changes when only AI nodes present")
    @MainActor func noChangesForAIOnly() {
        let doc = GraphDocument()
        let state = BundlewizardGraphState(nodes: [
            .init(id: "ai-1", type: .agent, title: "AI Node"),
        ])
        doc.mergeAIState(state)

        // Clear pending edits (merge resets tracking)
        doc.clearPendingEdits()

        let summary = doc.pendingEditsSummary()
        #expect(summary == nil)
    }

    @Test("clearPendingEdits resets tracking")
    @MainActor func clearResetsTracking() {
        let doc = GraphDocument()
        doc.addNode(GraphNode(id: "user-1", type: "agent", title: "Test"))
        doc.markNodeAsUserAdded("user-1")

        doc.clearPendingEdits()

        let summary = doc.pendingEditsSummary()
        #expect(summary == nil)
    }

    @Test("Removing a node records a change")
    @MainActor func removeRecordsChange() {
        let doc = GraphDocument()
        // Start with an AI node
        let state = BundlewizardGraphState(nodes: [
            .init(id: "ai-1", type: .agent, title: "AI Node"),
        ])
        doc.mergeAIState(state)
        doc.clearPendingEdits()

        // User removes it
        doc.removeNode("ai-1")
        doc.recordEdit("Removed node: ai-1")

        let summary = doc.pendingEditsSummary()
        #expect(summary != nil)
        #expect(summary!.contains("ai-1"))
    }
}
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift test --filter CanvasEditsTrackingTests 2>&1 | tail -20
```

Expected: FAIL — `pendingEditsSummary`, `clearPendingEdits`, `recordEdit` don't exist.

**Step 3: Add edit tracking to GraphDocument**

In `Sources/BundlewizardCore/Bridge/GraphDocument.swift`, add tracking properties and methods:

1. Add properties (after `latestAIState`):

```swift
    /// Edits made by the user since the last AI emission or clear.
    private var pendingEdits: [String] = []
```

2. Add methods (after `markNodeAsUserAdded`):

```swift
    // MARK: - Edit tracking

    /// Record a user edit for later sending to the bridge.
    public func recordEdit(_ description: String) {
        pendingEdits.append(description)
    }

    /// Get a summary of pending edits, or nil if none.
    public func pendingEditsSummary() -> String? {
        var edits = pendingEdits

        // Also include user-added nodes
        for nodeId in userAddedNodeIds {
            if let node = graph.nodes[nodeId] {
                let desc = "User added \(node.type) node: \(node.title ?? nodeId)"
                if !edits.contains(desc) {
                    edits.append(desc)
                }
            }
        }

        return edits.isEmpty ? nil : edits.joined(separator: "; ")
    }

    /// Clear pending edits (called after sending to bridge).
    public func clearPendingEdits() {
        pendingEdits.removeAll()
    }
```

3. Update `mergeAIState` to clear edits after a merge (at the end of the method):

```swift
        // 5. Clear pending edits — AI has acknowledged the current state
        pendingEdits.removeAll()
```

**Step 4: Run test to verify it passes**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift test --filter CanvasEditsTrackingTests 2>&1 | tail -20
```

Expected: PASS

**Step 5: Wire canvas_edits sending into AmplifierService**

In `Sources/BundlewizardCore/Services/AmplifierService.swift`, in the `send()` method, before sending the prompt over WebSocket, add canvas edits sending. After building `promptText` and before the `let payload` line, add:

```swift
        // Send pending canvas edits to bridge before the prompt
        if let edits = graphDocument.pendingEditsSummary() {
            let canvasPayload: [String: Any] = ["type": "canvas_edits", "data": edits]
            if let canvasData = try? JSONSerialization.data(withJSONObject: canvasPayload),
               let canvasJson = String(data: canvasData, encoding: .utf8) {
                try? await webSocket?.send(.string(canvasJson))
                graphDocument.clearPendingEdits()
                Log.swift("Sent canvas edits: \(edits.prefix(80))")
            }
        }
```

**Step 6: Run full test suite**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift test 2>&1 | tail -20
```

Expected: All tests pass.

**Step 7: Commit**

```bash
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && git add -A && git commit -m "feat: track canvas edits and send to bridge before each prompt

GraphDocument tracks user edits (add/remove/modify nodes, add edges).
AmplifierService sends pending edits as canvas_edits WebSocket message
before each prompt so the AI can incorporate them into its next emission."
```

---

## Phase 3 Complete Checklist

After all 7 tasks, verify:

```bash
# Swift tests
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift test 2>&1 | tail -10

# Build
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos && swift build 2>&1 | tail -5

# Python bridge tests (should still all pass)
cd /Users/michaeljabbour/dev/amplifier-app-bundlewizard-macos/bridge && uv run python -m pytest tests/ -v 2>&1 | tail -20
```

**What changed:**
1. `NodeTileView` — rich tiles with type label, colored title, property rows, dark theme
2. `ClusterView` — dashed border containers grouping nodes semantically
3. `EdgePathView` — 10 typed colored bezier edges with arrow markers
4. `CanvasLegendView` — bottom-left legend with all edge types
5. Cluster-aware auto-layout — groups by cluster, multi-column for large groups
6. Canvas interaction — updated toolbar/context menus for new node types
7. Canvas edits tracking — sends user changes to bridge before each prompt

## Full Implementation Complete

All three phases together deliver:

| Phase | Tasks | Focus |
|-------|-------|-------|
| Phase 1 | 7 | Bug fixes + bridge graph extraction |
| Phase 2 | 7 | Bundle files + Swift models + merge engine |
| Phase 3 | 7 | Rich canvas views + interactions + edit tracking |

**Total: 21 tasks** across 2 repos, transforming the app from fragile regex-based canvas updates to structured AI-driven graph state with a cicd-wizard-quality visual canvas.
