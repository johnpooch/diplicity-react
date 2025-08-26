const TestMap = () => {
    return (
        <svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
            {/* Root rectangle defining the map boundaries */}
            <rect width="800" height="600" fill="#f0f8ff" stroke="#333" strokeWidth="2" />

            {/* Provinces */}
            {/* Province 1: Coastal Province */}
            <path d="M 100 100 L 200 100 L 250 150 L 200 200 L 100 200 L 50 150 Z"
                fill="#90EE90" stroke="#333" strokeWidth="1" />
            <circle cx="150" cy="150" r="3" fill="#FF0000" /> {/* Supply center */}
            <text x="150" y="145" textAnchor="middle" fontSize="12" fill="#333">Coastal</text>
            <text x="150" y="160" textAnchor="middle" fontSize="10" fill="#666">Province</text>

            {/* Province 2: Mountain Province */}
            <path d="M 300 100 L 400 100 L 450 150 L 400 200 L 300 200 L 250 150 Z"
                fill="#DDA0DD" stroke="#333" strokeWidth="1" />
            <circle cx="350" cy="150" r="2" fill="#000" /> {/* Center point */}
            <text x="350" y="145" textAnchor="middle" fontSize="12" fill="#333">Mountain</text>

            {/* Province 3: Forest Province (no supply center) */}
            <path d="M 500 100 L 600 100 L 650 150 L 600 200 L 500 200 L 450 150 Z"
                fill="#228B22" stroke="#333" strokeWidth="1" />
            <circle cx="550" cy="150" r="2" fill="#000" /> {/* Center point */}
            <text x="550" y="145" textAnchor="middle" fontSize="12" fill="#333">Forest</text>

            {/* Impassable Province */}
            <path d="M 100 300 L 200 300 L 250 350 L 200 400 L 100 400 L 50 350 Z"
                fill="#696969" stroke="#333" strokeWidth="1" />
            <text x="150" y="345" textAnchor="middle" fontSize="12" fill="#FFF">Impassable</text>

            {/* Borders */}
            {/* Border between Coastal and Mountain provinces */}
            <path d="M 200 100 L 250 150 L 200 200"
                stroke="#FF0000" strokeWidth="3" fill="none" />

            {/* Border between Mountain and Forest provinces */}
            <path d="M 400 100 L 450 150 L 400 200"
                stroke="#FF0000" strokeWidth="3" fill="none" />

            {/* Border around impassable province */}
            <path d="M 100 300 L 200 300 L 250 350 L 200 400 L 100 400 L 50 350 Z"
                stroke="#FF0000" strokeWidth="2" fill="none" />

            {/* Legend */}
            <text x="650" y="50" fontSize="14" fontWeight="bold" fill="#333">Legend:</text>
            <circle cx="650" cy="70" r="3" fill="#FF0000" />
            <text x="660" y="75" fontSize="12" fill="#333">Supply Center</text>
            <circle cx="650" cy="90" r="2" fill="#000" />
            <text x="660" y="95" fontSize="12" fill="#333">Province Center</text>
            <path d="M 645 110 L 655 110" stroke="#FF0000" strokeWidth="3" />
            <text x="660" y="115" fontSize="12" fill="#333">Border</text>
        </svg>
    );
};

export { TestMap };