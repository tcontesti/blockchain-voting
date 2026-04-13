import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { WalletProvider, WalletManager, WalletId, NetworkId } from '@txnlab/use-wallet-react';
import App from './App';
import './index.css';
import './i18n';
import { ThemeProvider } from './theme/ThemeProvider';

const walletManager = new WalletManager({
  wallets: [
    // KMD: used for LocalNet development (pre-funded accounts from AlgoKit sandbox)
    {
      id: WalletId.KMD,
      options: {
        wallet: 'unencrypted-default-wallet',
        baseServer: 'http://localhost',
        token: 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
        port: 4002,
      },
    },
    // Pera: used for TestNet / MainNet
    WalletId.PERA,
  ],
  defaultNetwork: NetworkId.LOCALNET,
  networks: {
    [NetworkId.LOCALNET]: {
      algod: {
        baseServer: 'http://localhost',
        port: 4001,
        token: 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
      },
    },
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ThemeProvider>
      <WalletProvider manager={walletManager}>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </WalletProvider>
    </ThemeProvider>
  </React.StrictMode>,
);
