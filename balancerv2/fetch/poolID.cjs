const { ethers } = require("ethers");

const provider = new ethers.providers.JsonRpcProvider("https://mainnet.infura.io/v3/5f960a322d10455197483e07b53297fa
");
const poolAddress = "0x29d7a7e0d781c957696697b94d4bc18c651e358e"; // 例如 ACX/wstETH

const weightedPoolAbi = [
    {
        "inputs": [],
        "name": "getPoolId",
        "outputs": [{ "internalType": "bytes32", "name": "", "type": "bytes32" }],
        "stateMutability": "view",
        "type": "function"
    }
];

const getPoolId = async () => {
    const poolContract = new ethers.Contract(poolAddress, weightedPoolAbi, provider);
    const poolId = await poolContract.getPoolId();
    console.log("Pool ID:", poolId);
};

getPoolId();
