function showToast(message, type = "success", toastId = "operationToast") {
    const toastEl = document.getElementById(toastId);
    if (!toastEl) return; // на всякий случай

    const toastBody = toastEl.querySelector(".toast-body");
    const toast = new bootstrap.Toast(toastEl);

    toastBody.textContent = message;
    toastEl.classList.remove("bg-success", "bg-danger", "bg-warning", "text-white", "text-dark");

    if (type === "success") toastEl.classList.add("bg-success", "text-white");
    else if (type === "error") toastEl.classList.add("bg-danger", "text-white");
    else if (type === "warning") toastEl.classList.add("bg-warning", "text-dark");

    toast.show();
}
