interface PageContainerProps {
  children: React.ReactNode;
}

const PageContainer = ({ children }: PageContainerProps) => {
  return (
    <div className="flex-1 overflow-auto">
      <div className="container mx-auto px-6 py-8">
        {children}
      </div>
    </div>
  );
};

export default PageContainer;
