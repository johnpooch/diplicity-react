import { useMap } from "../../common";
import { QueryContainer } from "../query-container";

const Map: React.FC = () => {
  const { query } = useMap();
  return (
    <QueryContainer query={query}>
      {(data) => (
        <div
          dangerouslySetInnerHTML={{ __html: data }}
          style={{
            maxWidth: "100%",
            //maxHeight: "100%",
          }}
        />
      )}
    </QueryContainer>
  );
};

export { Map };
