function board() {
    return {
        tasks: [],
        showCreateForm: false,
        newTask: { title: "", description: "", planned_start: "", duration_days: 1 },
        columns: [
            { key: "backlog", label: "Backlog" },
            { key: "in_progress", label: "In Progress" },
            { key: "review", label: "Review" },
            { key: "done", label: "Done" },
        ],

        async loadTasks() {
            const res = await fetch("/api/tasks");
            this.tasks = await res.json();
            // Wait for Alpine to render the new cards, then (re)attach drag-drop.
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

        initSortable() {
            document.querySelectorAll(".card-list").forEach((el) => {
                // Avoid attaching Sortable twice to the same element.
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
                            body: JSON.stringify({
                                column: newColumn,
                                position: newIndex,
                            }),
                        });

                        if (!res.ok) {
                            const err = await res.json();
                            alert("Move failed: " + JSON.stringify(err.detail));
                        }
                        // Reload regardless -- to get fresh computed status/dates
                        // and to snap back visually if the move was rejected.
                        await this.loadTasks();
                    },
                });
            });
        },
    };
}