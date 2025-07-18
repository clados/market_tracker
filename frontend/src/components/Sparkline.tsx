import { LineChart, Line, ResponsiveContainer } from 'recharts';
import { PricePoint } from '../types/market';

interface SparklineProps {
  data: PricePoint[];
  color?: string;
  height?: number;
}

export const Sparkline: React.FC<SparklineProps> = ({ 
  data, 
  color = '#10b981', 
  height = 40 
}) => {
  if (!data || data.length === 0) return null;

  const chartData = data.map(point => ({
    value: point.price * 100 // Convert to percentage
  }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={chartData}>
        <Line 
          type="monotone" 
          dataKey="value" 
          stroke={color} 
          strokeWidth={2}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
};