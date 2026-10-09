function board() {
    return {
        tasks: [],
        showCreateForm: false,
        showBreakdownForm: false,
        showSuggestionsPanel: false,
        showExplainPanel: false,

        newTask: { title: "", description: "", planned_start: "", duration_days: 1 },
        breakdownDescription: "",
        breakdownStartDate: "",
        breakdownLoading: false,

        currentSuggestions: [],
        suggestionsForTaskId: null,
        suggestionsForTaskTitle: "",
        suggestionsLoading: false,

        criticalPathData: null,
        criticalPathSummary: "",
        criticalPathTaskIds: [],

        explainData: {},
        showDepForm: false,
        depTaskId: null,
        depTaskTitle: "",
        depPrereqId: "",

        columns: [
            { key: "backlog", label: "Backlog" },
            { key: "in_progress", label: "In Progress" },
            { key: "review", label: "Review" },
            { key: "done", label: "Done" },
        ],

        async loadTasks() {
            const res = await fetch("/api/tasks");
            this.tasks = await res.json();
            this.$nextTick(() => this.initSortable());
        },

        tasksByColumn(colKey) {
            return this.tasks
                .filter(t => t.column === colKey)
                .sort((a, b) => a.position - b.position);
        },

        async createTask() {
            const payload = {
                title: this.newTask.title,
                description: this.newTask.description,
                column: "backlog",
                position: this.tasksByColumn("backlog").length,
                planned_start: this.newTask.planned_start,
                duration_days: this.newTask.duration_days,
            };
            const res = await fetch("/api/tasks", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
            if (res.ok) {
                this.showCreateForm = false;
                this.newTask = { title: "", description: "", planned_start: "", duration_days: 1 };
                await this.loadTasks();
            } else {
                const err = await res.json();
                alert("Failed to create task: " + JSON.stringify(err.detail));
            }
        },

        async submitBreakdown() {
            if (!this.breakdownDescription.trim()) {
                alert("Please describe the feature first.");
                return;
            }
            this.breakdownLoading = true;
            try {
                const payload = {
                    feature_description: this.breakdownDescription,
                    planned_start: this.breakdownStartDate || new Date().toISOString().slice(0, 10),
                };
                const res = await fetch("/api/breakdown", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload),
                });
                if (res.ok) {
                    const result = await res.json();
                    this.showBreakdownForm = false;
                    this.breakdownDescription = "";
                    await this.loadTasks();
                    alert(`Created ${result.tasks_created.length} sub-tasks with ${result.dependencies_created.length} dependencies.`);
                } else {
                    const err = await res.json();
                    alert("Failed to generate breakdown: " + JSON.stringify(err.detail));
                }
            } finally {
                this.breakdownLoading = false;
            }
        },

        async suggestDependencies(taskId) {
            const task = this.tasks.find(t => t.id === taskId);
            this.suggestionsForTaskId = taskId;
            this.suggestionsForTaskTitle = task ? task.title : "";
            this.showSuggestionsPanel = true;
            this.suggestionsLoading = true;
            this.currentSuggestions = [];

            try {
                await fetch(`/api/tasks/${taskId}/suggest-dependencies`, { method: "POST" });
                await this.loadSuggestionsFor(taskId);
            } catch (e) {
                alert("Failed to get suggestions.");
            } finally {
                this.suggestionsLoading = false;
            }
        },

        async loadSuggestionsFor(taskId) {
            const res = await fetch(`/api/tasks/${taskId}/suggestions`);
            const all = await res.json();
            const pending = all.filter(s => s.status === "pending");
            // Attach prerequisite title for display.
            this.currentSuggestions = pending.map(s => {
                const prereqTask = this.tasks.find(t => t.id === s.suggested_prerequisite_id);
                return { ...s, prerequisite_title: prereqTask ? prereqTask.title : `Task #${s.suggested_prerequisite_id}` };
            });
        },

        async approveSuggestion(suggestionId) {
            const res = await fetch(`/api/tasks/suggestions/${suggestionId}/approve`, { method: "POST" });
            if (res.ok) {
                await this.loadSuggestionsFor(this.suggestionsForTaskId);
                await this.loadTasks();
            } else {
                const err = await res.json();
                alert("Approve failed: " + JSON.stringify(err.detail));
            }
        },

        async rejectSuggestion(suggestionId) {
            await fetch(`/api/tasks/suggestions/${suggestionId}/reject`, { method: "POST" });
            await this.loadSuggestionsFor(this.suggestionsForTaskId);
        },

        openDependencyForm(taskId) {
            const t = this.tasks.find(x => x.id === taskId);
            this.depTaskId = taskId;
            this.depTaskTitle = t ? t.title : "";
            this.depPrereqId = "";
            this.showDepForm = true;
        },

        availablePrereqs() {
            return this.tasks.filter(t => t.id !== this.depTaskId);
        },

        async addDependency() {
            if (!this.depPrereqId) {
                alert("Select a prerequisite first.");
                return;
            }
            const res = await fetch("/api/dependencies", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    task_id: this.depTaskId,
                    prerequisite_id: Number(this.depPrereqId),
                }),
            });
            if (res.ok) {
                this.showDepForm = false;
                await this.loadTasks();
            } else {
                const err = await res.json();
                alert("Cannot add dependency: " + (typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail)));
            }
        },

        async explainStatus(taskId) {
            const res = await fetch(`/api/tasks/${taskId}/explain-status`);
            this.explainData = await res.json();
            this.showExplainPanel = true;
        },

        async showCriticalPath() {
            const res = await fetch("/api/critical-path");
            this.criticalPathData = await res.json();
            this.criticalPathTaskIds = this.criticalPathData.path.map(p => p.id);
            this.criticalPathSummary = this.criticalPathData.path.map(p => p.title).join(" → ");
        },

        async whatIfPreview(taskId) {
            const newDuration = prompt("Enter hypothetical new duration (days):");
            if (!newDuration || isNaN(newDuration)) return;
            const res = await fetch("/api/what-if", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ task_id: taskId, new_duration_days: parseInt(newDuration) }),
            });
            if (res.ok) {
                const result = await res.json();
                if (result.changes.length === 0) {
                    alert("No downstream impact -- nothing else would shift.");
                } else {
                    const lines = result.changes.map(c => `${c.title}: shifts by ${c.shift_days} day(s) (new end: ${c.new_end})`);
                    alert(`Project end: ${result.project_end_before} → ${result.project_end_after}\n\n` + lines.join("\n"));
                }
            } else {
                alert("What-if preview failed.");
            }
        },

        initSortable() {
            document.querySelectorAll(".card-list").forEach((el) => {
                if (el._sortableInstance) return;
                el._sortableInstance = new Sortable(el, {
                    group: "board",
                    animation: 150,
                    onEnd: async (evt) => {
                        const taskId = parseInt(evt.item.dataset.taskId, 10);
                        const newColumn = evt.to.dataset.column;
                        const newIndex = evt.newIndex;
                        const res = await fetch(`/api/tasks/${taskId}`, {
                            method: "PATCH",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ column: newColumn, position: newIndex }),
                        });
                        if (!res.ok) {
                            const err = await res.json();
                            alert("Move failed: " + JSON.stringify(err.detail));
                        }
                        await this.loadTasks();
                    },
                });
            });
        },
    };
}