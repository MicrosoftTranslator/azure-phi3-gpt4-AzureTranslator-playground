import logo from "./logo.svg";
import { useState } from "react";

import "./App.css";
import { AssistantPanel } from "./AssistantPanel";

function App() {
  const [useMT, toggleUseMT] = useState(false);

  return (
    <div>
      <div className="App">
        <AssistantPanel useMT={useMT} toggleUseMT={toggleUseMT} />
      </div>
    </div>
  );
}

export default App;
