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
                alert("Failed to create task");
            }
        },
    };
}