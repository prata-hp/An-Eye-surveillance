export function formatStatus(status = "") {
  return status
    .replaceAll("_", " ")
    .toUpperCase();
}


export function getStatusClass(status = "") {
  switch (status) {
    case "NEW":
      return "status-new";

    case "UNDER_REVIEW":
      return "status-review";

    case "PENDING":
      return "status-pending";

    case "ESCALATED":
      return "status-escalated";

    case "FALSE_POSITIVE":
      return "status-false";

    case "RESOLVED":
      return "status-resolved";

    default:
      return "status-default";
  }
}
