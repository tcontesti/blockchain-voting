import { useState } from 'react';
import { useWallet } from '@txnlab/use-wallet-react';
import { Wallet, LogOut, ChevronDown, ChevronUp, Check } from 'lucide-react';

function truncateAddress(addr: string): string {
  return `${addr.slice(0, 4)}...${addr.slice(-4)}`;
}

const WALLET_LABELS: Record<string, string> = {
  kmd: 'KMD (LocalNet)',
  pera: 'Pera Wallet',
};

export function WalletConnect() {
  const { wallets, activeAddress } = useWallet();
  const [menuOpen, setMenuOpen] = useState(false);

  const connectedWallet = wallets.find((w) => w.isConnected);

  const handleConnect = async (walletId: string) => {
    const wallet = wallets.find((w) => w.id === walletId);
    if (!wallet) return;
    try {
      await wallet.connect();
    } catch {
      localStorage.removeItem('txnlab-use-wallet');
      try {
        await wallet.connect();
      } catch (retryErr) {
        console.error('Wallet connect failed after state reset:', retryErr);
      }
    }
    setMenuOpen(false);
  };

  const handleSwitchAccount = (address: string) => {
    if (!connectedWallet) return;
    connectedWallet.setActiveAccount(address);
    setMenuOpen(false);
  };

  const handleDisconnect = async () => {
    if (connectedWallet) await connectedWallet.disconnect();
    localStorage.removeItem('txnlab-use-wallet');
    setMenuOpen(false);
  };

  // ── Not connected ────────────────────────────────────────────────
  if (!activeAddress) {
    return (
      <div className="relative">
        <button
          onClick={() => setMenuOpen(!menuOpen)}
          className="inline-flex h-9 items-center gap-2 rounded-full border border-border bg-surface px-4 text-sm font-medium text-fg transition hover:border-primary hover:text-primary"
        >
          <Wallet size={15} />
          <span className="hidden sm:inline">Connect</span>
          {menuOpen ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
        </button>

        {menuOpen && (
          <>
            <div className="fixed inset-0 z-40" onClick={() => setMenuOpen(false)} />
            <div className="absolute right-0 top-full z-50 mt-2 w-52 rounded-xl border border-border bg-surface p-2 shadow-md">
              <div className="mb-1 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-muted">
                Choose wallet
              </div>
              {wallets.map((wallet) => (
                <button
                  key={wallet.id}
                  onClick={() => handleConnect(wallet.id)}
                  className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-fg transition hover:bg-bg"
                >
                  <Wallet size={14} className="text-primary" />
                  {WALLET_LABELS[wallet.id] ?? wallet.metadata.name}
                </button>
              ))}
            </div>
          </>
        )}
      </div>
    );
  }

  // ── Connected ────────────────────────────────────────────────────
  const accounts = connectedWallet?.accounts ?? [];
  const hasMultiple = accounts.length > 1;

  return (
    <div className="relative">
      <button
        onClick={() => setMenuOpen(!menuOpen)}
        className="inline-flex h-9 items-center gap-2 rounded-full border border-primary/40 bg-primary/10 px-4 text-sm font-medium text-primary transition hover:bg-primary/20"
      >
        <span className="h-2 w-2 rounded-full bg-emerald-500" />
        <span className="font-mono text-xs">{truncateAddress(activeAddress)}</span>
        <ChevronDown size={14} />
      </button>

      {menuOpen && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setMenuOpen(false)} />
          <div className="absolute right-0 top-full z-50 mt-2 w-64 rounded-xl border border-border bg-surface p-2 shadow-md">

            {/* Account switcher — only shown when wallet has multiple accounts */}
            {hasMultiple && (
              <>
                <div className="mb-1 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-muted">
                  Switch account
                </div>
                {accounts.map((account) => {
                  const isActive = account.address === activeAddress;
                  return (
                    <button
                      key={account.address}
                      onClick={() => handleSwitchAccount(account.address)}
                      className={`flex w-full items-center gap-2 rounded-lg px-3 py-2 text-xs transition hover:bg-bg ${
                        isActive ? 'text-primary' : 'text-fg'
                      }`}
                    >
                      <span className="flex h-5 w-5 shrink-0 items-center justify-center">
                        {isActive ? (
                          <Check size={13} className="text-primary" />
                        ) : (
                          <span className="h-1.5 w-1.5 rounded-full bg-border" />
                        )}
                      </span>
                      <span className="font-mono">
                        {account.address.slice(0, 6)}...{account.address.slice(-4)}
                      </span>
                    </button>
                  );
                })}
                <div className="my-1.5 border-t border-border" />
              </>
            )}

            {/* Single account display when no switching available */}
            {!hasMultiple && (
              <div className="px-3 py-2 font-mono text-xs text-muted">
                {activeAddress.slice(0, 10)}...{activeAddress.slice(-6)}
              </div>
            )}

            <button
              onClick={handleDisconnect}
              className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-fg transition hover:bg-bg"
            >
              <LogOut size={14} />
              Disconnect
            </button>
          </div>
        </>
      )}
    </div>
  );
}
