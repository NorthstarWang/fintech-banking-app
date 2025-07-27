import React from 'react';
import { motion } from 'framer-motion';
import Card from '../ui/Card';
import { ChevronRight } from 'lucide-react';

interface Column<T> {
  key: string;
  header: string;
  render: (item: T) => React.ReactNode;
  mobileLabel?: string;
  mobilePrimary?: boolean;
  mobileHide?: boolean;
  align?: 'left' | 'center' | 'right';
  width?: string;
}

interface ResponsiveTableProps<T> {
  data: T[];
  columns: Column<T>[];
  keyExtractor: (item: T, index: number) => string;
  onRowClick?: (item: T) => void;
  emptyMessage?: string;
  className?: string;
  mobileBreakpoint?: string;
  loading?: boolean;
  cardVariant?: 'default' | 'prominent' | 'subtle';
}

export function ResponsiveTable<T>({
  data,
  columns,
  keyExtractor,
  onRowClick,
  emptyMessage = 'No data available',
  className = '',
  mobileBreakpoint = 'md',
  loading = false,
  cardVariant = 'subtle',
}: ResponsiveTableProps<T>) {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.05,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 },
  };

  if (loading) {
    return (
      <div className={`space-y-3 ${className}`}>
        {[...Array(3)].map((_, i) => (
          <div
            key={i}
            className="h-24 rounded-lg bg-[rgba(var(--glass-rgb),0.1)] animate-pulse"
          />
        ))}
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <Card variant="default" className={className}>
        <div className="p-12 text-center">
          <p className="text-[var(--text-2)]">{emptyMessage}</p>
        </div>
      </Card>
    );
  }

  return (
    <>
      {/* Desktop Table */}
      <div className={`hidden ${mobileBreakpoint}:block ${className}`}>
        <Card variant="default" padding="none">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[var(--border-1)]">
                  {columns.map((column) => (
                    <th
                      key={column.key}
                      className={`
                        px-6 py-4 text-xs font-semibold text-[var(--text-2)] uppercase tracking-wider
                        ${column.align === 'center' ? 'text-center' : ''}
                        ${column.align === 'right' ? 'text-right' : ''}
                        ${column.width || ''}
                      `}
                    >
                      {column.header}
                    </th>
                  ))}
                  {onRowClick && (
                    <th className="w-8"></th>
                  )}
                </tr>
              </thead>
              <tbody>
                {data.map((item, index) => (
                  <tr
                    key={keyExtractor(item, index)}
                    className={`
                      border-b border-[var(--border-1)] last:border-b-0
                      ${onRowClick ? 'hover:bg-[rgba(var(--glass-rgb),0.1)] cursor-pointer transition-colors' : ''}
                    `}
                    onClick={() => onRowClick?.(item)}
                  >
                    {columns.map((column) => (
                      <td
                        key={column.key}
                        className={`
                          px-6 py-4 text-sm text-[var(--text-1)]
                          ${column.align === 'center' ? 'text-center' : ''}
                          ${column.align === 'right' ? 'text-right' : ''}
                        `}
                      >
                        {column.render(item)}
                      </td>
                    ))}
                    {onRowClick && (
                      <td className="px-4">
                        <ChevronRight className="w-4 h-4 text-[var(--text-2)]" />
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      {/* Mobile Cards */}
      <motion.div
        className={`${mobileBreakpoint}:hidden space-y-3 ${className}`}
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {data.map((item, index) => {
          const primaryColumn = columns.find(col => col.mobilePrimary) || columns[0];
          const visibleColumns = columns.filter(col => !col.mobileHide);

          return (
            <motion.div
              key={keyExtractor(item, index)}
              variants={itemVariants}
              whileTap={onRowClick ? { scale: 0.98 } : {}}
            >
              <Card
                variant={cardVariant}
                onClick={onRowClick ? () => onRowClick(item) : undefined}
                hoverable={!!onRowClick}
                className="relative"
              >
                <div className="p-4">
                  {/* Primary content */}
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <div className="font-medium text-[var(--text-1)] text-base">
                        {primaryColumn.render(item)}
                      </div>
                    </div>
                    {onRowClick && (
                      <ChevronRight className="w-5 h-5 text-[var(--text-2)] ml-2 flex-shrink-0" />
                    )}
                  </div>

                  {/* Secondary content */}
                  <div className="space-y-2">
                    {visibleColumns
                      .filter(col => col.key !== primaryColumn.key)
                      .map((column) => (
                        <div key={column.key} className="flex items-center justify-between text-sm">
                          <span className="text-[var(--text-2)]">
                            {column.mobileLabel || column.header}
                          </span>
                          <span className="text-[var(--text-1)] font-medium">
                            {column.render(item)}
                          </span>
                        </div>
                      ))}
                  </div>
                </div>
              </Card>
            </motion.div>
          );
        })}
      </motion.div>
    </>
  );
}

export default ResponsiveTable;