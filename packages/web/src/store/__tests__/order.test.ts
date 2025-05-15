import { orderSlice } from "../order";

const { updateOrder } = orderSlice.actions;

test("should set source when order is empty", () => {
    const initialState = {};
    const action = updateOrder("lon");
    const newState = orderSlice.reducer(initialState, action);

    expect(newState).toEqual({ source: "lon" });
});

test("should set type when order has source", () => {
    const initialState = { source: "lon" };
    const action = updateOrder("move");
    const newState = orderSlice.reducer(initialState, action);
    expect(newState).toEqual({ source: "lon", type: "move" });
});

test("should set target when order has source and type and type is Move", () => {
    const initialState = { source: "lon", type: "Move" };
    const action = updateOrder("par");
    const newState = orderSlice.reducer(initialState, action);
    expect(newState).toEqual({ source: "lon", type: "Move", target: "par" });
});

test("should set aux when order has source and type and type is Support", () => {
    const initialState = { source: "lon", type: "Support" };
    const action = updateOrder("par");
    const newState = orderSlice.reducer(initialState, action);
    expect(newState).toEqual({ source: "lon", type: "Support", aux: "par" });
});

test("should set aux when order has source and type and type is Convoy", () => {
    const initialState = { source: "lon", type: "Convoy" };
    const action = updateOrder("par");
    const newState = orderSlice.reducer(initialState, action);
    expect(newState).toEqual({ source: "lon", type: "Convoy", aux: "par" });
});

test("should set target when order has source, type and aux and type is Support", () => {
    const initialState = { source: "lon", type: "Support", aux: "par" };
    const action = updateOrder("par");
    const newState = orderSlice.reducer(initialState, action);
    expect(newState).toEqual({ source: "lon", type: "Support", aux: "par", target: "par" });
});

test("should set target when order has source, type and aux and type is Convoy", () => {
    const initialState = { source: "lon", type: "Convoy", aux: "par" };
    const action = updateOrder("par");
    const newState = orderSlice.reducer(initialState, action);
    expect(newState).toEqual({ source: "lon", type: "Convoy", aux: "par", target: "par" });
});


test("selectIsComplete should return false when order is empty", () => {
    const result = orderSlice.selectors.selectIsComplete({ order: {} });
    expect(result).toEqual(false);
});

test("selectIsComplete should return false when order has source", () => {
    const result = orderSlice.selectors.selectIsComplete({ order: { source: "lon" } });
    expect(result).toEqual(false);
});

test("selectIsComplete should return true when order has source and type is Hold", () => {
    const result = orderSlice.selectors.selectIsComplete({ order: { source: "lon", type: "Hold" } });
    expect(result).toEqual(true);
});

test("selectIsComplete should return true when order has source and type is Build", () => {
    const result = orderSlice.selectors.selectIsComplete({ order: { source: "lon", type: "Build" } });
    expect(result).toEqual(true);
});

test("selectIsComplete should return true when order has source and type is Disband", () => {
    const result = orderSlice.selectors.selectIsComplete({ order: { source: "lon", type: "Disband" } });
    expect(result).toEqual(true);
});

test("selectIsComplete should return false when order has source and type is Move", () => {
    const result = orderSlice.selectors.selectIsComplete({ order: { source: "lon", type: "Move" } });
    expect(result).toEqual(false);
});

test("selectIsComplete should return false when order has source and type is Support", () => {
    const result = orderSlice.selectors.selectIsComplete({ order: { source: "lon", type: "Support" } });
    expect(result).toEqual(false);
});

test("selectIsComplete should return false when order has source and type is Convoy", () => {
    const result = orderSlice.selectors.selectIsComplete({ order: { source: "lon", type: "Convoy" } });
    expect(result).toEqual(false);
});

test("selectIsComplete should return true when order has source, type and target and type is Move", () => {
    const result = orderSlice.selectors.selectIsComplete({ order: { source: "lon", type: "Move", target: "par" } });
    expect(result).toEqual(true);
});

test("selectIsComplete should return false when order has source, type and aux and type is Support", () => {
    const result = orderSlice.selectors.selectIsComplete({ order: { source: "lon", type: "Support", aux: "par" } });
    expect(result).toEqual(false);
});

test("selectIsComplete should return false when order has source, type and auxt and type is Convoy", () => {
    const result = orderSlice.selectors.selectIsComplete({ order: { source: "lon", type: "Convoy", aux: "par" } });
    expect(result).toEqual(false);
});

test("selectIsComplete should return true when order has source, type and aux and target and type is Support", () => {
    const result = orderSlice.selectors.selectIsComplete({ order: { source: "lon", type: "Support", aux: "par", target: "par" } });
    expect(result).toEqual(true);
});

test("selectIsComplete should return true when order has source, type and aux and target and type is Convoy", () => {
    const result = orderSlice.selectors.selectIsComplete({ order: { source: "lon", type: "Convoy", aux: "par", target: "par" } });
    expect(result).toEqual(true);
});

test("selectStep should return source when order is empty", () => {
    const result = orderSlice.selectors.selectStep({ order: {} });
    expect(result).toEqual("source");
});

test("selectStep should return type when order has source", () => {
    const result = orderSlice.selectors.selectStep({ order: { source: "lon" } });
    expect(result).toEqual("type");
});

test("selectStep should return aux when order has source, type Support and no aux", () => {
    const result = orderSlice.selectors.selectStep({ order: { source: "lon", type: "Support" } });
    expect(result).toEqual("aux");
});

test("selectStep should return aux when order has source, type Convoy and no aux", () => {
    const result = orderSlice.selectors.selectStep({ order: { source: "lon", type: "Convoy" } });
    expect(result).toEqual("aux");
});

test("selectStep should return target when order has source, type Support and aux", () => {
    const result = orderSlice.selectors.selectStep({ order: { source: "lon", type: "Support", aux: "par" } });
    expect(result).toEqual("target");
});

test("selectStep should return target when order has source, type Convoy and aux", () => {
    const result = orderSlice.selectors.selectStep({ order: { source: "lon", type: "Convoy", aux: "par" } });
    expect(result).toEqual("target");
});

test("selectStep should return target when order has source and type Move", () => {
    const result = orderSlice.selectors.selectStep({ order: { source: "lon", type: "Move" } });
    expect(result).toEqual("target");
});

test("selectStep should return target when order has source and type Hold", () => {
    const result = orderSlice.selectors.selectStep({ order: { source: "lon", type: "Hold" } });
    expect(result).toEqual("target");
});





