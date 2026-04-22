import { RouterProvider } from "react-router-dom";

import { AppProviders } from "./providers";
import { appRouter } from "./router";
import "./styles.css";

export function App() {
  return (
    <AppProviders>
      <RouterProvider router={appRouter} />
    </AppProviders>
  );
}
