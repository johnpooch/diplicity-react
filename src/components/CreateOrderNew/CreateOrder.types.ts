type Node = {
    name: string;
    icon?: React.ReactNode;
    children: { [id: string]: Node };
};

type CreateOrderInjectedProps = {
    options: { [id: string]: Node };
    onSubmit: (selectedOptions: string[]) => void;
    onClose: () => void;
};

type CreateOrderStatus = {
    source?: { name: string; icon?: React.ReactNode };
    orderType?: { name: string; icon?: React.ReactNode };
    target?: { name: string; icon?: React.ReactNode };
    aux?: { name: string; icon?: React.ReactNode };
    isComplete: boolean;
}

export type { CreateOrderInjectedProps, CreateOrderStatus, Node };