// GAIA Shell — Entry Point
import './shell/Shell.css';
import { mountShell } from './shell/Shell';

const root = document.querySelector<HTMLDivElement>('#app');
if (!root) throw new Error('[GAIA] #app root element not found.');

mountShell(root);
