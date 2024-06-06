function websiteStatus() {
    return {
        isLoading: true,
        statuses: [],
        intervals: [],
        fetchData() {
            Promise.all([
                fetch("api/website").then((response) => response.json()),
                fetch("api/status").then((response) => response.json()),
            ])
                .then(([websites, statuses]) => {
                    this.statuses = websites.data.map((site) => ({
                        ...site,
                        status: statuses[site.url] || "Warning",
                        timer: this.getIntervalTime(statuses[site.url] || "Warning"),
                    }));
                    this.isLoading = false;
                    this.startIntervals();
                })
                .catch((error) => {
                    console.error("Error fetching data:", error);
                    this.isLoading = false;
                });
        },
        getIntervalTime(status) {
            switch (status) {
                case "Up":
                    return 60;
                case "Down":
                    return 30;
                case "Warning":
                    return 20;
                default:
                    return 60;
            }
        },
        statusClass(status) {
            return {
                "text-success": status === "Up",
                "text-danger": status === "Down",
                "text-warning": status === "Warning",
            };
        },

        startIntervals() {
            this.statuses.forEach((site, index) => {
                this.intervals[index] = setInterval(() => {
                    if (site.timer > 0) {
                        site.timer--;
                    } else {
                        this.updateStatus(site.url, index);
                    }
                }, 1000);
            });
        },
        updateStatus(url, index) {
            fetch(`/api/status?url=${encodeURIComponent(url)}`)
                .then((response) => {
                    if (!response.ok) {
                        throw new Error("Network response was not ok");
                    }
                    return response.json();
                })
                .then((data) => {
                    const newStatus = data[url] || "Warning";
                    this.statuses[index].status = newStatus;
                    this.statuses[index].timer = this.getIntervalTime(newStatus);
                    this.statuses[index].lastUpdate = new Date().toLocaleString();
                })
                .catch((error) => {
                    console.error("Error updating status:", error);
                    this.statuses[index].timer = this.getIntervalTime("Warning");
                    this.statuses[index].lastUpdate = new Date().toLocaleString();
                });
        },
    };
}
