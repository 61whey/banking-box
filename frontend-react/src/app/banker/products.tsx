import { useEffect, useState } from 'react'
import { BankerLayout } from '@/components/layouts/banker-layout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { bankerAPI } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import type { Product } from '@/types/api'
import { Package } from 'lucide-react'

export default function BankerProducts() {
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const { toast } = useToast()

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        const data = await bankerAPI.getProducts()
        // Убеждаемся что data это массив
        const productsArray = Array.isArray(data) ? data : []
        setProducts(productsArray)
      } catch (error: any) {
        toast({
          title: 'Ошибка загрузки',
          description: error.response?.data?.detail || 'Не удалось загрузить продукты',
          variant: 'destructive',
        })
      } finally {
        setLoading(false)
      }
    }

    fetchProducts()
  }, [toast])

  return (
    <BankerLayout title="Банковские продукты">
      {loading ? (
        <p className="text-muted-foreground">Загрузка...</p>
      ) : products.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <p className="text-center text-muted-foreground">Нет продуктов</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {products.map((product) => (
            <Card key={product.product_id}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <Package className="h-8 w-8 text-primary" />
                  <span className={`px-2 py-1 text-xs rounded ${
                    product.is_active 
                      ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                      : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
                  }`}>
                    {product.is_active ? 'Активен' : 'Неактивен'}
                  </span>
                </div>
                <CardTitle className="mt-4">{product.name}</CardTitle>
                <CardDescription>
                  <span className="inline-block px-2 py-1 text-xs bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 rounded">
                    {product.product_type}
                  </span>
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground mb-4">{product.description}</p>
                <div className="space-y-2 text-sm">
                  {product.interest_rate && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Ставка:</span>
                      <span className="font-medium">{product.interest_rate}%</span>
                    </div>
                  )}
                  {product.min_amount && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Мин. сумма:</span>
                      <span className="font-medium">{product.min_amount.toLocaleString('ru-RU')} ₽</span>
                    </div>
                  )}
                  {product.max_amount && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Макс. сумма:</span>
                      <span className="font-medium">{product.max_amount.toLocaleString('ru-RU')} ₽</span>
                    </div>
                  )}
                  {product.term_months && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Срок:</span>
                      <span className="font-medium">{product.term_months} мес.</span>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </BankerLayout>
  )
}

