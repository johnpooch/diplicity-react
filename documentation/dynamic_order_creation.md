# Dynamic Order Creation

This document describes a feature for dynamic order creation.

## API Endpoints

### OrderableProvincesList

This endpoint lists the provinces that the user can order for the current phase.

#### URL
```
GET /game/<game-id>/orderable-provinces
```

#### Example

Response:
```
[
    {
        province: {
            "id": "nap",
            "name": "Naples",
            "type": "coastal",
            "supplyCenter": true
        },
        order: {
            ...
        }
    },
]
```

#### Behaviour
- The order should be undefined if no order exists for the province

### OrderCreate

This endpoint takes a partially or fully complete order and returns the available options as well as some other data to power the UI. If the order is complete, the order is saved to the backend.

#### URL
```
POST /games/{gameId}/orders/create-interactive
```

#### Example (Partial)

Request:
```
{
    selected: ["bud", "Move"]
}
```

Response:
```
{
  "completed": false,
  "step": "select-destination",
  "title": "Select province to move to",
  "options": [...],
  "canGoBack": true
}
```

#### Example (Complete)

Request:
```
{
    province: "bud",
    selected: ["Move", "tri"]
}
```

Response:
```
{
  "completed": true,
  "step": "completed",
  "title": "Budapest will move to Trieste",
  "options": [],
  "canGoBack": false
}
```

## Approach

### Options Service

Defined a service which is responsible for traversing the options tree.

```
class OptionsService:
  def __init__(self, options):
    self.options = options

  def list_options_for_nation(self, nation):
    # Lists the orderable provinces for the given nation
    pass

  def list_options_for_selected(self, nation, partial_order):
    # Lists the options based on the partially completed order. Also includes step id
    # Returns: { options: [...], step: "select-order-type" }
    pass
```

This service should be comprehensively tested.

### OrderCreateView

OrderCreateView should be modified to take a `selected` property which is a list of strings.

The view should use a new serializer for its return value called `OrderCreateResponseSerializer`.
