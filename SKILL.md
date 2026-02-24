---
name: excalidraw
description: >
  Generate Excalidraw diagrams from text descriptions. Supports flowcharts,
  architecture diagrams, sequence diagrams, mind maps, timelines, and ER diagrams.
  Auto-detects the optimal diagram type or accepts explicit requests.
  Outputs .excalidraw source files + PNG exports. Integrates with Obsidian vault.
  Triggers: excalidraw, diagram, flowchart, architecture diagram, sequence diagram,
  mind map, timeline, ER diagram, visualize, draw, visualize this, diagram this.
  DON'T use when: user wants ASCII art, Mermaid/PlantUML syntax, or data charts
  (bar, pie, line graphs).
---

# Excalidraw Diagram Skill

Generate professional diagrams from natural language. The agent analyzes the input,
writes a Python script using the diagram API, renders it, and delivers PNG + source.

## Paths

```
SKILL_DIR = ~/.openclaw/workspace/skills/excalidraw
SCRIPTS   = $SKILL_DIR/scripts
OBSIDIAN  = $OBSIDIAN_DIAGRAMS_DIR  (optional)
```

## Workflow

### Step 1: Detect diagram type

Run the router to get a suggestion (or decide yourself from the user's prompt):

```bash
python3 $SCRIPTS/diagram_router.py "user's text here"
# → {"diagram_type": "flowchart", "confidence": 0.85, "reasoning": "..."}
```

If the user explicitly says "flowchart" or "sequence diagram", skip detection and use their choice.

### Step 2: Write the diagram script

Write a Python script to `/tmp/excalidraw_<timestamp>.py` using the appropriate diagram class.
Use the examples below as templates — copy the pattern, replace the content.

**Critical:** Always include this import block at the top:

```python
#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.expanduser("~/.openclaw/workspace/skills/excalidraw/scripts"))
from excalidraw_generator import (
    Diagram, Flowchart, AutoLayoutFlowchart, ArchitectureDiagram,
    SequenceDiagram, MindMap, TimelineDiagram, ERDiagram,
    DiagramStyle, FlowchartStyle, ArchitectureStyle, BoxStyle, LayoutConfig
)
```

### Step 3: Run the script

```bash
python3 /tmp/excalidraw_<timestamp>.py
```

This produces the `.excalidraw` file.

### Step 4: Export, deliver, clean up

```bash
python3 $SCRIPTS/export_and_deliver.py \
  --input /tmp/diagram_name.excalidraw \
  --obsidian \
  --name diagram_name \
  --output-dir /tmp \
  --cleanup /tmp/excalidraw_<timestamp>.py
```

This:
- Validates the diagram
- Exports to PNG via Playwright
- Copies .excalidraw + .png to Obsidian vault
- Deletes the temp Python script
- Returns JSON with all paths

### Step 5: Send to Discord

Use the message tool to send the PNG:
```
message(action="send", media="/tmp/diagram_name.png", message="Here's the diagram")
```

---

## Diagram Type Examples

Each example below is a complete, tested script. Copy the pattern, replace the content.

### 1. Flowchart (AutoLayout)

**Use when:** steps, processes, decisions, if/then/else, numbered steps, workflows

```python
#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.expanduser("~/.openclaw/workspace/skills/excalidraw/scripts"))
from excalidraw_generator import AutoLayoutFlowchart, DiagramStyle, FlowchartStyle, LayoutConfig

fc = AutoLayoutFlowchart(
    diagram_style=DiagramStyle(roughness=0),
    flowchart_style=FlowchartStyle(
        start_color="cyan",
        end_color="red",
        process_color="blue",
        decision_color="orange",
    ),
    layout_config=LayoutConfig(vertical_spacing=100, horizontal_spacing=80),
)

# Nodes — use shape="ellipse" for start/end, "diamond" for decisions, default rectangle for process
fc.add_node("start", "User Opens App", shape="ellipse", color="cyan", node_type="terminal")
fc.add_node("check_auth", "Logged In?", shape="diamond", color="orange", node_type="decision")
fc.add_node("dashboard", "Show Dashboard", color="blue", node_type="process")
fc.add_node("login_page", "Show Login Page", color="blue", node_type="process")
fc.add_node("enter_creds", "Enter Credentials", color="blue", node_type="process")
fc.add_node("validate", "Valid?", shape="diamond", color="orange", node_type="decision")
fc.add_node("redirect", "Redirect to Dashboard", color="green", node_type="process")
fc.add_node("error", "Show Error", color="red", node_type="process")
fc.add_node("end", "End", shape="ellipse", color="red", node_type="terminal")

# Edges — label decision branches with "Yes"/"No"
fc.add_edge("start", "check_auth")
fc.add_edge("check_auth", "dashboard", label="Yes")
fc.add_edge("check_auth", "login_page", label="No")
fc.add_edge("login_page", "enter_creds")
fc.add_edge("enter_creds", "validate")
fc.add_edge("validate", "redirect", label="Yes")
fc.add_edge("validate", "error", label="No")
fc.add_edge("error", "enter_creds", label="Retry")
fc.add_edge("dashboard", "end")
fc.add_edge("redirect", "end")

fc.compute_layout(two_column=True, target_aspect_ratio=0.8)
fc.save("/tmp/auth_flow.excalidraw")
print("Saved: /tmp/auth_flow.excalidraw")
```

### 2. Architecture Diagram

**Use when:** system components, services, databases, APIs, infrastructure, client-server

```python
#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.expanduser("~/.openclaw/workspace/skills/excalidraw/scripts"))
from excalidraw_generator import ArchitectureDiagram, DiagramStyle, ArchitectureStyle

arch = ArchitectureDiagram(
    diagram_style=DiagramStyle(roughness=0),
    architecture_style=ArchitectureStyle(
        component_color="blue",
        database_color="green",
        service_color="violet",
        user_color="gray",
    ),
)

# Layout: top-to-bottom layers, x controls horizontal position
# Row 1: Client
arch.user("client", "Browser Client", x=350, y=50)

# Row 2: Gateway
arch.service("gateway", "API Gateway", x=300, y=180, color="violet")

# Row 3: Services (spread horizontally)
arch.service("auth", "Auth Service", x=50, y=350, color="blue")
arch.service("users", "User Service", x=250, y=350, color="blue")
arch.service("orders", "Order Service", x=450, y=350, color="blue")
arch.service("notify", "Notification Service", x=650, y=350, color="cyan")

# Row 4: Data stores
arch.database("authdb", "Auth DB", x=50, y=520, color="green")
arch.database("userdb", "User DB", x=250, y=520, color="green")
arch.database("orderdb", "Order DB", x=450, y=520, color="green")
arch.component("queue", "Message Queue", x=600, y=480, color="orange")

# Connections (label with protocol/method)
arch.connect("client", "gateway", "HTTPS")
arch.connect("gateway", "auth", "gRPC")
arch.connect("gateway", "users", "gRPC")
arch.connect("gateway", "orders", "gRPC")
arch.connect("auth", "authdb", "SQL")
arch.connect("users", "userdb", "SQL")
arch.connect("orders", "orderdb", "SQL")
arch.connect("orders", "queue", "publish")
arch.connect("queue", "notify", "subscribe")

arch.save("/tmp/microservices.excalidraw")
print("Saved: /tmp/microservices.excalidraw")
```

### 3. Sequence Diagram

**Use when:** message flows between actors/services, request-response, API calls, protocols

```python
#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.expanduser("~/.openclaw/workspace/skills/excalidraw/scripts"))
from excalidraw_generator import SequenceDiagram, DiagramStyle

seq = SequenceDiagram(
    participant_spacing=220,
    message_spacing=70,
    diagram_style=DiagramStyle(roughness=0),
)

# Add participants left-to-right in the order they first appear
seq.participant("client", "Browser", color="gray")
seq.participant("api", "API Gateway", color="violet")
seq.participant("auth", "Auth Service", color="blue")
seq.participant("db", "User DB", color="green")

# Messages in chronological order
seq.message("client", "api", "POST /login (email, password)")
seq.message("api", "auth", "validateCredentials()")
seq.message("auth", "db", "SELECT user WHERE email=?")
seq.message("db", "auth", "user record")
seq.message("auth", "auth", "verify password hash")  # self-message: use same from/to
seq.message("auth", "api", "JWT token")
seq.message("api", "client", "200 OK + Set-Cookie")

# Notes for context
seq.note("auth", "bcrypt comparison\ntakes ~100ms", position="right")

seq.save("/tmp/login_sequence.excalidraw")
print("Saved: /tmp/login_sequence.excalidraw")
```

**Self-messages:** Use `seq.self_message("participant_id", "label")` for internal actions.

**Dashed returns:** Use `seq.message("b", "a", "response", style="dashed")` for return messages.

### 4. Mind Map

**Use when:** brainstorming, topic breakdown, categories, concepts branching from a central idea

```python
#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.expanduser("~/.openclaw/workspace/skills/excalidraw/scripts"))
from excalidraw_generator import MindMap, DiagramStyle

mm = MindMap(diagram_style=DiagramStyle(roughness=1))  # roughness=1 for hand-drawn feel

# Central concept
mm.central("Machine Learning", color="violet")

# Main branches (level 1) — returns branch_id for adding sub-branches
b1 = mm.branch("__central__", "Supervised", color="blue")
b2 = mm.branch("__central__", "Unsupervised", color="green")
b3 = mm.branch("__central__", "Reinforcement", color="orange")

# Sub-branches (level 2)
mm.leaf(b1, "Classification")
mm.leaf(b1, "Regression")
mm.leaf(b1, "Neural Networks")

mm.leaf(b2, "Clustering")
mm.leaf(b2, "Dimensionality Reduction")
mm.leaf(b2, "Anomaly Detection")

mm.leaf(b3, "Q-Learning")
mm.leaf(b3, "Policy Gradient")
mm.leaf(b3, "Multi-Agent")

mm.save("/tmp/ml_mindmap.excalidraw")
print("Saved: /tmp/ml_mindmap.excalidraw")
```

**Note:** The central node ID is always `"__central__"`. Branch IDs are returned by `mm.branch()`.

### 5. Timeline

**Use when:** chronological events, history, milestones, project phases, evolution over time

```python
#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.expanduser("~/.openclaw/workspace/skills/excalidraw/scripts"))
from excalidraw_generator import TimelineDiagram, DiagramStyle

tl = TimelineDiagram(
    direction="horizontal",  # or "vertical"
    event_spacing=200,
    diagram_style=DiagramStyle(roughness=0),
)

# Events in chronological order
tl.event("2008", "Whitepaper Published", "Satoshi Nakamoto publishes Bitcoin whitepaper", color="blue")
tl.milestone("2009", "Genesis Block", color="red")  # milestones use diamond shape
tl.event("2010", "First Transaction", "10,000 BTC for two pizzas", color="green")
tl.event("2013", "First Bull Run", "Price reaches $1,000", color="orange")
tl.event("2017", "$20K ATH", "Bitcoin hits $20,000", color="orange")
tl.milestone("2021", "$69K ATH", color="red")
tl.event("2024", "ETF Approved", "SEC approves spot Bitcoin ETFs", color="violet")

tl.save("/tmp/bitcoin_timeline.excalidraw")
print("Saved: /tmp/bitcoin_timeline.excalidraw")
```

**Periods (time spans):** Use `tl.period("2017", "2020", "Crypto Winter", color="gray")` for date ranges.

### 6. ER Diagram

**Use when:** database schema, entities, relationships, data models, tables with attributes

```python
#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.expanduser("~/.openclaw/workspace/skills/excalidraw/scripts"))
from excalidraw_generator import ERDiagram, DiagramStyle

er = ERDiagram(
    entity_spacing=300,
    diagram_style=DiagramStyle(roughness=0),
)

# Entities with attributes
er.entity("user", "User", attributes=["id (PK)", "name", "email", "password_hash", "created_at"], color="blue")
er.entity("post", "Post", attributes=["id (PK)", "title", "content", "user_id (FK)", "published_at"], color="green")
er.entity("comment", "Comment", attributes=["id (PK)", "body", "user_id (FK)", "post_id (FK)", "created_at"], color="orange")
er.entity("tag", "Tag", attributes=["id (PK)", "name"], color="violet")

# Relationships with cardinality
er.relationship("user", "post", "writes", cardinality="1:N")
er.relationship("user", "comment", "writes", cardinality="1:N")
er.relationship("post", "comment", "has", cardinality="1:N")
er.relationship("post", "tag", "tagged with", cardinality="N:M")

er.save("/tmp/blog_schema.excalidraw")
print("Saved: /tmp/blog_schema.excalidraw")
```

### 7. Simple Diagram (freeform)

**Use when:** quick diagrams, custom layouts, anything that doesn't fit the specialized types

```python
#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.expanduser("~/.openclaw/workspace/skills/excalidraw/scripts"))
from excalidraw_generator import Diagram, DiagramStyle

d = Diagram(diagram_style=DiagramStyle(roughness=0))

# Title
d.text_box(250, 20, "Data Pipeline", font_size=28, color="black")

# Boxes — position with (x, y), connect with arrow_between
source = d.box(50, 100, "Raw Data", color="gray")
ingest = d.box(250, 100, "Ingest", color="blue")
transform = d.box(450, 100, "Transform", color="violet")
store = d.box(650, 100, "Data Lake", color="green", shape="ellipse")

# Arrows with labels
d.arrow_between(source, ingest, "CSV/JSON")
d.arrow_between(ingest, transform, "validated")
d.arrow_between(transform, store, "parquet")

# Second row
analytics = d.box(450, 250, "Analytics", color="orange")
dashboard = d.box(650, 250, "Dashboard", color="cyan")

d.arrow_between(store, analytics, "query")
d.arrow_between(analytics, dashboard, "metrics")

d.save("/tmp/data_pipeline.excalidraw")
print("Saved: /tmp/data_pipeline.excalidraw")
```

---

## Styling Options

### Roughness
- `0` — Clean, precise lines (professional/technical)
- `1` — Hand-drawn look (default, casual)
- `2` — Rough sketch (whiteboard feel)

### Colors
`blue`, `green`, `red`, `yellow`, `orange`, `violet`, `cyan`, `teal`, `gray`, `black`

### Shapes (for `box()`)
`rectangle` (default), `ellipse`, `diamond`

### Font Families (for BoxStyle)
`hand` (default), `normal`, `code`, `excalifont`, `nunito`, `comic`

### Color Schemes (for DiagramStyle)
`default`, `monochrome`, `corporate`, `vibrant`, `earth`

Access scheme colors: `d.scheme_color("primary")`, `d.scheme_color("accent")`, etc.

---

## Positioning Guide

- **Grid alignment:** Use multiples of 50 for x,y coordinates
- **Horizontal spacing:** 200px between components
- **Vertical spacing:** 150px between rows/layers
- **Box sizes:** Default 150×60, use wider for long labels
- **Architecture layouts:** Top=clients, middle=services, bottom=data

---

## Viewing Output

1. **Excalidraw.com** — drag .excalidraw file onto https://excalidraw.com
2. **VS Code** — install "Excalidraw" extension, open the file
3. **Obsidian** — install Excalidraw plugin, files saved to `Resources/diagrams/`
4. **macOS** — `open filename.excalidraw` opens with default app
