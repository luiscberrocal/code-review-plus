from datetime import datetime
import re

from code_review.git.schemas import BranchSchema


def create_branch_schema(git_line: str) -> BranchSchema:
    """Create a BranchSchema instance."""
    regex_pattern = re.compile(
        r"^(?P<name>[\w\s.]+) "  # Match the name (one or more words and spaces, with periods)
        r"(?P<date>[A-Za-z]{3}\s+[A-Za-z]{3}\s+\d+\s+\d{2}:\d{2}:\d{2}\s+\d{4}\s+[-+]\d{4}) " # Match the full date format
        r"Merge\s+(?:branch|tag)\s+'?(?P<branch>[^']+)'?\s+into\s+'?(?P<target_branch>.*)'?$" # Match 'Merge branch/tag 'branch' into 'target''
    )
    match = regex_pattern.match(git_line)
    if match:
        data = match.groupdict()
        name = match.group("name").strip()
        date = match.group("date").strip()
        branch = match.group("branch").strip()
        date_string = data["date"]
        try:
            # Use strptime to parse the date string based on the known format.
            parsed_date = datetime.strptime(date_string, "%a %b %d %H:%M:%S %Y %z")
        except ValueError as e:
            print(f"Error parsing date string '{date_string}': {e}")
            parsed_date = None
        return BranchSchema(name=branch, author=name, date=parsed_date)
    else:
        raise ValueError(f"Invalid git line format: {git_line}")


if __name__ == '__main__':
    log_data = """Joel Borrero Wed Jun 18 12:48:46 2025 -0500 Merge tag 'v9.1.3' into develop
    Joel Borrero Wed Jun 18 12:31:05 2025 -0500 Merge branch 'feature/vpop-194_create_payment_providers_for_colombia' into develop
    elio.linarez Mon Jun 16 11:33:07 2025 -0500 Merge tag 'v9.1.2' into develop
    elio.linarez Mon Jun 16 11:25:10 2025 -0500 Merge branch 'bugfix/VPOP-212_Error_screen' into develop
    Luis C. Berrocal Thu Jun 12 12:38:35 2025 -0500 Merge tag 'v9.1.1' into develop
    Luis C. Berrocal Wed Jun 11 13:34:18 2025 -0500 Merge tag 'v9.1.0' into develop
    Luis C. Berrocal Wed Jun 11 13:33:34 2025 -0500 Merge branch 'feature/vpop-211_task_refactoring' into develop
    elio.linarez Wed Jun 11 08:23:34 2025 -0500 Merge tag 'v9.0.2' into develop
    elio.linarez Wed Jun 11 08:20:16 2025 -0500 Merge branch 'feature/vpop-174-178-180-adjustments-for-cb-and-cl-balance-equal-to-0' into develop
    Luis C. Berrocal Tue Jun 10 14:09:37 2025 -0500 Merge tag 'v9.0.1' into develop
    Luis C. Berrocal Tue Jun 10 10:57:50 2025 -0500 Merge tag 'v9.0.0' into develop
    Luis C. Berrocal Tue Jun 10 10:57:00 2025 -0500 Merge branch 'feature/vpop-126_pending_indexes' into develop
    Luis C. Berrocal Tue Jun 10 06:30:30 2025 -0500 Merge tag 'v8.0.0' into develop
    Luis C. Berrocal Tue Jun 10 06:29:08 2025 -0500 Merge branch 'feature/vpop-126_action_indexes' into develop
    Artem Shakhov Mon Jun 9 19:05:46 2025 +0000 Merge branch 'feature/separate-ci-image-tags' into 'develop'
    Luis C. Berrocal Mon Jun 9 11:47:12 2025 -0500 Merge tag 'v7.0.0' into develop
    Luis C. Berrocal Mon Jun 9 11:46:30 2025 -0500 Merge branch 'feature/vpop-126_add_indexes_action_logs' into develop
    Luis C. Berrocal Mon Jun 9 07:57:27 2025 -0500 Merge tag 'v6.0.0' into develop
    Luis C. Berrocal Mon Jun 9 07:56:36 2025 -0500 Merge branch 'feature/vpop-126_squashing_migrations' into develop
    Luis C. Berrocal Mon Jun 9 06:16:41 2025 -0500 Merge tag 'v5.0.1' into develop
    Artem Shakhov Fri Jun 6 21:34:59 2025 +0000 Merge branch 'OPS-2196' into 'develop'
    Luis C. Berrocal Thu Jun 5 08:38:04 2025 -0500 Merge tag 'v5.0.0' into develop
    Luis C. Berrocal Thu Jun 5 08:37:17 2025 -0500 Merge branch 'feature/vpop-126_adding_indexes' into develop
    elio.linarez Wed Jun 4 14:49:29 2025 -0500 Merge branch 'master' into develop
    Luis C. Berrocal Wed Jun 4 11:49:24 2025 -0500 Merge tag 'v4.2.1' into develop
    Luis C. Berrocal Wed Jun 4 09:00:40 2025 -0500 Merge tag 'v4.2.0' into develop
    Luis C. Berrocal Wed Jun 4 09:00:00 2025 -0500 Merge branch 'feature/vpop-197_update_pj_django_payments' into develop
    elio.linarez Mon Jun 2 12:45:11 2025 -0500 Merge tag 'v4.1.0' into develop
    elio.linarez Mon Jun 2 12:44:19 2025 -0500 Merge branch 'feature/VPOP-200_Remove_data_gt_90_days' into develop
    Luis C. Berrocal Mon Jun 2 09:09:26 2025 -0500 Merge tag 'v4.0.1' into develop"""

    # Call the function to parse the data.
    lines = log_data.split("\n")
    for line in lines:
        results = create_branch_schema(line)
        print(results)


