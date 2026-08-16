---
paths:
  - "service/**/constants.py"
  - "service/**/models.py"
  - "service/**/serializers.py"
---

# Constants

Constants live in `service/common/constants.py`. Reference them by class attribute (`GameStatus.ACTIVE`), never by raw string (`"active"`).

```python
class GameStatus:
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"

    STATUS_CHOICES = (
        (PENDING, "Pending"),
        (ACTIVE, "Active"),
        (COMPLETED, "Completed"),
        (ABANDONED, "Abandoned"),
    )
```
